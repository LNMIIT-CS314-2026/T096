from typing import Optional, List
from models.verification import Verification
from repositories.database import get_db_connection

class VerificationRepository:
    def save(self, ver: Verification) -> None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO verifications (verification_id, activity_id, verified_by, decision, comments, decision_date)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(verification_id) DO UPDATE SET
                decision = excluded.decision,
                comments = excluded.comments
            """,
            (
                ver.verificationId,
                ver.activityId,
                ver.verifiedBy,
                ver.decision.value if hasattr(ver.decision, "value") else str(ver.decision),
                ver.comments,
                ver.decisionDate
            )
        )
        conn.commit()
        conn.close()

    def findByActivityId(self, activityId: str) -> List[Verification]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM verifications WHERE activity_id = ? ORDER BY decision_date DESC", (activityId,))
        rows = cursor.fetchall()
        conn.close()
        return [
            Verification(
                verificationId=r["verification_id"],
                activityId=r["activity_id"],
                verifiedBy=r["verified_by"],
                decision=r["decision"],
                comments=r["comments"] or "",
                decisionDate=r["decision_date"]
            )
            for r in rows
        ]
