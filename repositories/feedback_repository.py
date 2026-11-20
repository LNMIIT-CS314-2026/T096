import sqlite3
from typing import List, Optional
from datetime import datetime
from models.feedback import FeedbackForm, FeedbackResponse
from repositories.database import get_db_connection

class FeedbackRepository:
    """
    Persistence operations for Feedback Forms and Responses (FR-036 - FR-040).
    Enforces duplicate prevention at database level (FR-039).
    Supports opens_at / closes_at date windows (FR-037, BR-011).
    """
    def saveForm(self, form: FeedbackForm) -> None:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Migrate schema if columns not yet present
        try:
            cursor.execute("ALTER TABLE feedback_forms ADD COLUMN opens_at TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE feedback_forms ADD COLUMN closes_at TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        cursor.execute(
            """
            INSERT INTO feedback_forms (form_id, title, activity_id, target_role, is_open, created_by, created_at, opens_at, closes_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(form_id) DO UPDATE SET
                title = excluded.title,
                is_open = excluded.is_open,
                opens_at = excluded.opens_at,
                closes_at = excluded.closes_at
            """,
            (
                form.formId,
                form.title,
                form.activityId,
                form.targetRole,
                1 if form.isOpen else 0,
                form.createdBy,
                form.createdAt,
                form.opensAt,
                form.closesAt
            )
        )
        conn.commit()
        conn.close()

    def _row_to_form(self, row) -> FeedbackForm:
        keys = row.keys()
        return FeedbackForm(
            formId=row["form_id"],
            title=row["title"],
            activityId=row["activity_id"],
            targetRole=row["target_role"],
            isOpen=bool(row["is_open"]),
            createdBy=row["created_by"],
            createdAt=row["created_at"],
            opensAt=row["opens_at"] if "opens_at" in keys else None,
            closesAt=row["closes_at"] if "closes_at" in keys else None
        )

    def findFormById(self, formId: str) -> Optional[FeedbackForm]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM feedback_forms WHERE form_id = ?", (formId,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return self._row_to_form(row)

    def findAllForms(self, onlyOpen: bool = False) -> List[FeedbackForm]:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM feedback_forms"
        if onlyOpen:
            query += " WHERE is_open = 1"
        query += " ORDER BY created_at DESC"
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_form(r) for r in rows]

    def hasUserSubmitted(self, formId: str, userId: str) -> bool:
        """FR-039: Checks if user has already submitted this feedback form."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM feedback_responses WHERE form_id = ? AND user_id = ?", (formId, userId))
        row = cursor.fetchone()
        conn.close()
        return row is not None

    def saveResponse(self, response: FeedbackResponse) -> bool:
        """Saves feedback response with duplicate prevention constraint (FR-039) and Student-only role check."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Enforce that only students can submit responses (SRS Section 11.1 & UC-019)
            cursor.execute("SELECT role FROM users WHERE user_id = ?", (response.userId,))
            user_row = cursor.fetchone()
            if user_row and user_row["role"] != "STUDENT":
                return False

            cursor.execute(
                """
                INSERT INTO feedback_responses (response_id, form_id, user_id, rating, comments, submitted_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    response.responseId,
                    response.formId,
                    response.userId,
                    response.rating,
                    response.comments,
                    response.submittedAt
                )
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def getResponsesByFormId(self, formId: str) -> List[FeedbackResponse]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM feedback_responses WHERE form_id = ? ORDER BY submitted_at DESC", (formId,))
        rows = cursor.fetchall()
        conn.close()
        return [
            FeedbackResponse(
                responseId=r["response_id"],
                formId=r["form_id"],
                userId=r["user_id"],
                rating=r["rating"],
                comments=r["comments"] or "",
                submittedAt=r["submitted_at"]
            )
            for r in rows
        ]
