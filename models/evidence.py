from datetime import datetime
from typing import Optional
from models.enums import VerificationStatus

class Evidence:
    """Evidence entity (Section 45.4.11)."""
    def __init__(
        self,
        evidenceId: str,
        activityId: str,
        fileName: str,
        fileType: str,
        fileSize: int,
        filePath: str,
        uploadedBy: str,
        description: str = "",
        verificationStatus: VerificationStatus | str = VerificationStatus.PENDING,
        uploadedAt: Optional[str] = None
    ):
        self.evidenceId = evidenceId
        self.activityId = activityId
        self.fileName = fileName
        self.fileType = fileType
        self.fileSize = fileSize
        self.filePath = filePath
        self.uploadedBy = uploadedBy
        self.description = description
        self.verificationStatus = (
            verificationStatus if isinstance(verificationStatus, VerificationStatus)
            else VerificationStatus(verificationStatus)
        )
        self.uploadedAt = uploadedAt or datetime.now().isoformat()

    def to_dict(self):
        return {
            "evidenceId": self.evidenceId,
            "activityId": self.activityId,
            "fileName": self.fileName,
            "fileType": self.fileType,
            "fileSize": self.fileSize,
            "filePath": self.filePath,
            "uploadedBy": self.uploadedBy,
            "description": self.description,
            "verificationStatus": self.verificationStatus.value,
            "uploadedAt": self.uploadedAt
        }
