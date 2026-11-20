import sqlite3
from typing import Optional, List
from datetime import datetime
from models.user import User, create_user_instance
from models.enums import Role, AccountStatus
from repositories.database import get_db_connection

class UserRepository:
    """Persistence operations for User Profile and Password authentication."""

    def save(self, user: User) -> None:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        created_at = user.createdAt or now
        updated_at = user.updatedAt or now

        cursor.execute(
            """
            INSERT INTO users (
                user_id, name, email, password_hash, role,
                department_id, contact_info, account_status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name = excluded.name,
                email = excluded.email,
                password_hash = excluded.password_hash,
                role = excluded.role,
                department_id = excluded.department_id,
                contact_info = excluded.contact_info,
                account_status = excluded.account_status,
                updated_at = excluded.updated_at
            """,
            (
                user.userId,
                user.name,
                user.email.strip().lower(),
                user.passwordHash,
                user.role.value if hasattr(user.role, "value") else str(user.role),
                user.departmentId if user.departmentId else None,
                user.contactInfo,
                user.accountStatus.value if hasattr(user.accountStatus, "value") else str(user.accountStatus),
                created_at,
                updated_at
            )
        )
        conn.commit()
        conn.close()

    def findById(self, userId: str) -> Optional[User]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (userId,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return self._row_to_user(row)

    def findByEmail(self, email: str) -> Optional[User]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return self._row_to_user(row)

    def findAll(self, departmentId: Optional[str] = None, role: Optional[str] = None) -> List[User]:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM users WHERE 1=1"
        params = []
        if departmentId:
            query += " AND department_id = ?"
            params.append(departmentId)
        if role:
            query += " AND role = ?"
            params.append(role)
        query += " ORDER BY name ASC"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_user(r) for r in rows]

    def updateProfile(self, userId: str, name: str, contactInfo: str, departmentId: Optional[str] = None) -> bool:
        """Updates user profile details."""
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            """
            UPDATE users 
            SET name = ?, contact_info = ?, department_id = ?, updated_at = ?
            WHERE user_id = ?
            """,
            (name.strip(), contactInfo.strip(), departmentId if departmentId else None, now, userId)
        )
        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return changed

    def updatePassword(self, userId: str, newPasswordHash: str) -> bool:
        """Updates user password hash."""
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            "UPDATE users SET password_hash = ?, updated_at = ? WHERE user_id = ?",
            (newPasswordHash, now, userId)
        )
        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return changed

    def updateRole(self, userId: str, newRole: Role | str) -> bool:
        conn = get_db_connection()
        cursor = conn.cursor()
        role_str = newRole.value if hasattr(newRole, "value") else str(newRole)
        now = datetime.now().isoformat()
        cursor.execute("UPDATE users SET role = ?, updated_at = ? WHERE user_id = ?", (role_str, now, userId))
        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return changed

    # --- OTP Storage for Google SMTP Authentication ---
    def saveOtp(self, email: str, otp_code: str, expires_at: datetime) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE otp_verifications SET is_used = 1 WHERE LOWER(email) = LOWER(?) AND is_used = 0", (email.strip(),))
        cursor.execute(
            """
            INSERT INTO otp_verifications (email, otp_code, expires_at, is_used, created_at)
            VALUES (?, ?, ?, 0, ?)
            """,
            (email.strip().lower(), otp_code, expires_at.isoformat(), datetime.now().isoformat())
        )
        otp_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return otp_id

    def verifyOtp(self, email: str, otp_code: str) -> bool:
        """Validates OTP: matches code, unexpired, and unused."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT otp_id, expires_at FROM otp_verifications
            WHERE LOWER(email) = LOWER(?) AND otp_code = ? AND is_used = 0
            ORDER BY otp_id DESC LIMIT 1
            """,
            (email.strip().lower(), otp_code.strip())
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False

        expires_at = datetime.fromisoformat(row["expires_at"])
        if datetime.now() > expires_at:
            conn.close()
            return False

        cursor.execute("UPDATE otp_verifications SET is_used = 1 WHERE otp_id = ?", (row["otp_id"],))
        conn.commit()
        conn.close()
        return True

    def _row_to_user(self, row: sqlite3.Row) -> User:
        return create_user_instance(
            userId=row["user_id"],
            name=row["name"],
            email=row["email"],
            passwordHash=row["password_hash"] or "",
            role=row["role"],
            departmentId=row["department_id"],
            contactInfo=row["contact_info"] or "",
            accountStatus=row["account_status"] or AccountStatus.ACTIVE.value,
            createdAt=row["created_at"],
            updatedAt=row["updated_at"]
        )
