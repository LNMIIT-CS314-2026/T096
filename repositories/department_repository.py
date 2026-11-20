from typing import List, Optional
from models.department import Department
from models.domain_area import DomainArea
from repositories.database import get_db_connection

class DepartmentRepository:
    def save(self, dept: Department) -> None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO departments (department_id, name, head_of_dept, contact_info)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(department_id) DO UPDATE SET
                name = excluded.name,
                head_of_dept = excluded.head_of_dept,
                contact_info = excluded.contact_info
            """,
            (dept.departmentId, dept.name, dept.headOfDept, dept.contactInfo)
        )
        conn.commit()
        conn.close()

    def findById(self, deptId: str) -> Optional[Department]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM departments WHERE department_id = ?", (deptId,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return Department(
            departmentId=row["department_id"],
            name=row["name"],
            headOfDept=row["head_of_dept"] or "",
            contactInfo=row["contact_info"] or ""
        )

    def findAll(self) -> List[Department]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM departments ORDER BY department_id ASC")
        rows = cursor.fetchall()
        conn.close()
        return [
            Department(
                departmentId=r["department_id"],
                name=r["name"],
                headOfDept=r["head_of_dept"] or "",
                contactInfo=r["contact_info"] or ""
            )
            for r in rows
        ]


class DomainAreaRepository:
    def save(self, domain: DomainArea) -> None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO domain_areas (domain_id, name, description)
            VALUES (?, ?, ?)
            ON CONFLICT(domain_id) DO UPDATE SET
                name = excluded.name,
                description = excluded.description
            """,
            (domain.domainId, domain.name, domain.description)
        )
        conn.commit()
        conn.close()

    def findById(self, domainId: str) -> Optional[DomainArea]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM domain_areas WHERE domain_id = ?", (domainId,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return DomainArea(domainId=row["domain_id"], name=row["name"], description=row["description"] or "")

    def delete(self, domainId: str) -> bool:
        """Deletes a domain area/criterion record."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM domain_areas WHERE domain_id = ?", (domainId,))
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        return rows_affected > 0

    def countLinkedActivities(self, domainId: str) -> int:
        """Counts how many activities are tagged with this criterion."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS cnt FROM activities WHERE domain_id = ?", (domainId,))
        row = cursor.fetchone()
        conn.close()
        return row["cnt"] if row else 0

    def getNextCriterionId(self) -> str:
        """
        Auto-generates the next sequential unique criterion ID: CRITERION-1, CRITERION-2, etc.
        """
        import re
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT domain_id FROM domain_areas")
        rows = cursor.fetchall()
        conn.close()

        existing_nums = set()
        for r in rows:
            m = re.search(r"(\d+)$", r["domain_id"])
            if m:
                existing_nums.add(int(m.group(1)))

        next_num = 1
        while next_num in existing_nums:
            next_num += 1

        return f"CRITERION-{next_num}"

    def findAll(self) -> List[DomainArea]:
        import re
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM domain_areas")
        rows = cursor.fetchall()
        conn.close()

        def _sort_key(r):
            m = re.search(r"(\d+)$", r["domain_id"])
            return (int(m.group(1)) if m else 9999, r["domain_id"])

        sorted_rows = sorted(rows, key=_sort_key)
        return [DomainArea(domainId=r["domain_id"], name=r["name"], description=r["description"] or "") for r in sorted_rows]
