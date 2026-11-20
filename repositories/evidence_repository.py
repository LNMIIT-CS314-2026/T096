from typing import Optional, List
from models.evidence import Evidence
from models.enums import VerificationStatus
from repositories.database import get_db_connection

class EvidenceRepository:
    def save(self, evidence: Evidence) -> None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO evidence (
                evidence_id, activity_id, file_name, file_type, file_size,
                file_path, description, verification_status, uploaded_by, uploaded_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(evidence_id) DO UPDATE SET
                file_name = excluded.file_name,
                verification_status = excluded.verification_status
            """,
            (
                evidence.evidenceId,
                evidence.activityId,
                evidence.fileName,
                evidence.fileType,
                evidence.fileSize,
                evidence.filePath,
                evidence.description,
                evidence.verificationStatus.value if hasattr(evidence.verificationStatus, "value") else str(evidence.verificationStatus),
                evidence.uploadedBy,
                evidence.uploadedAt
            )
        )
        conn.commit()
        conn.close()

    def findById(self, evidenceId: str) -> Optional[Evidence]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM evidence WHERE evidence_id = ?", (evidenceId,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return Evidence(
            evidenceId=row["evidence_id"],
            activityId=row["activity_id"],
            fileName=row["file_name"],
            fileType=row["file_type"],
            fileSize=row["file_size"],
            filePath=row["file_path"],
            uploadedBy=row["uploaded_by"],
            description=row["description"] or "",
            verificationStatus=row["verification_status"],
            uploadedAt=row["uploaded_at"]
        )

    def findByActivityId(self, activityId: str) -> List[Evidence]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM evidence WHERE activity_id = ? ORDER BY uploaded_at DESC", (activityId,))
        rows = cursor.fetchall()
        conn.close()
        return [
            Evidence(
                evidenceId=r["evidence_id"],
                activityId=r["activity_id"],
                fileName=r["file_name"],
                fileType=r["file_type"],
                fileSize=r["file_size"],
                filePath=r["file_path"],
                uploadedBy=r["uploaded_by"],
                description=r["description"] or "",
                verificationStatus=r["verification_status"],
                uploadedAt=r["uploaded_at"]
            )
            for r in rows
        ]

    def updateStatusByActivityId(self, activityId: str, status: VerificationStatus | str) -> None:
        conn = get_db_connection()
        cursor = conn.cursor()
        status_str = status.value if hasattr(status, "value") else str(status)
        cursor.execute("UPDATE evidence SET verification_status = ? WHERE activity_id = ?", (status_str, activityId))
        conn.commit()
        conn.close()

    def delete(self, evidenceId: str) -> bool:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM evidence WHERE evidence_id = ?", (evidenceId,))
        changed = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return changed
