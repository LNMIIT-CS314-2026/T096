import uuid
import os
from typing import Optional, List, Tuple
from models.evidence import Evidence
from models.enums import ActivityStatus, VerificationStatus, Role
from repositories.evidence_repository import EvidenceRepository
from repositories.activity_repository import ActivityRepository
from utils.file_validator import FileValidator
from utils.file_store import FileStoreAdapter
from services.notification_service import NotificationService
from services.history_service import HistoryService

MAX_EVIDENCE_PER_ACTIVITY = 5  # Strict cap on evidence documents per activity

class EvidenceService:
    """
    Section 47.2.4 Evidence & Verification Service (IEvidenceUpload).
    Uploads, validates, stores, and manages evidence files with full constraint checks,
    evidence file count cap, strict object-level authorization, and audit logging (FR-025 - FR-030, BR-008, BR-013).
    """
    def __init__(
        self,
        evidence_repo: Optional[EvidenceRepository] = None,
        activity_repo: Optional[ActivityRepository] = None,
        validator: Optional[FileValidator] = None,
        file_store: Optional[FileStoreAdapter] = None,
        notif_service: Optional[NotificationService] = None,
        history_service: Optional[HistoryService] = None
    ):
        self.evidence_repo = evidence_repo or EvidenceRepository()
        self.activity_repo = activity_repo or ActivityRepository()
        self.validator = validator or FileValidator()
        self.file_store = file_store or FileStoreAdapter()
        self.notif_service = notif_service or NotificationService()
        self.history_service = history_service or HistoryService()

    def uploadEvidence(
        self,
        activityId: str,
        userId: str,
        file_storage,
        description: str = ""
    ) -> Tuple[bool, str, Optional[Evidence]]:
        activity = self.activity_repo.findById(activityId)
        if not activity:
            return False, "Activity not found.", None

        # BR-008, BR-012: Lock check
        if not activity.canAcceptEvidence():
            return False, f"Activity is {activity.status.value}. Evidence cannot be added (BR-008, BR-012).", None

        # Constraint: Strict evidence upload limit per activity
        existing_evidence = self.evidence_repo.findByActivityId(activityId)
        if len(existing_evidence) >= MAX_EVIDENCE_PER_ACTIVITY:
            return False, f"Upload limit reached: An activity may have at most {MAX_EVIDENCE_PER_ACTIVITY} evidence documents attached.", None

        if not file_storage or not file_storage.filename:
            return False, "Please select a valid file to upload.", None

        # Character limit on description
        clean_desc = description.strip()
        if len(clean_desc) > 250:
            return False, "Evidence description cannot exceed 250 characters.", None

        filename = file_storage.filename
        file_ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""

        # Validate format (FR-026, BR-013)
        if not self.validator.checkFormat(file_ext):
            return False, "Unsupported format. Allowed: PDF, DOCX, JPG, PNG.", None

        # Validate size (FR-027, BR-013)
        file_storage.seek(0, os.SEEK_END)
        file_size = file_storage.tell()
        file_storage.seek(0)

        if not self.validator.checkSize(file_size):
            return False, "File exceeds the maximum size limit (10 MB). Upload rejected.", None

        # Save to disk using FileStoreAdapter
        try:
            saved_path = self.file_store.save(file_storage)
        except Exception:
            return False, "Upload failed. No evidence was saved. Please try again.", None

        ev_id = f"EV-{uuid.uuid4().hex[:6].upper()}"

        evidence = Evidence(
            evidenceId=ev_id,
            activityId=activityId,
            fileName=filename,
            fileType=file_ext.upper(),
            fileSize=file_size,
            filePath=saved_path,
            uploadedBy=userId,
            description=clean_desc,
            verificationStatus=VerificationStatus.PENDING
        )
        try:
            self.evidence_repo.save(evidence)
        except Exception:
            # Atomic rollback: delete orphaned file if DB save fails (NFR-016)
            self.file_store.remove(saved_path)
            return False, "Storage error: could not record evidence metadata in database.", None

        # Update activity status to EVIDENCE_UPLOADED (FR-022)
        if activity.status in [ActivityStatus.ASSIGNED, ActivityStatus.IN_PROGRESS, ActivityStatus.RETURNED]:
            activity.status = ActivityStatus.EVIDENCE_UPLOADED
            self.activity_repo.save(activity)

        # Record upload in activity history log (Collaboration UC-008 Seq 5, FR-051)
        self.history_service.recordChange(
            activityId=activityId,
            userId=userId,
            action="Evidence Uploaded",
            oldValue=None,
            newValue=f"{filename} ({ev_id})"
        )

        # Notify coordinator (FR-044)
        if activity.createdBy:
            self.notif_service.notify(
                activity.createdBy,
                "VERIFICATION",
                f"Evidence uploaded for '{activity.title}' by user {userId}."
            )

        return True, "Evidence uploaded. Status updated to 'Evidence Uploaded'.", evidence

    def deleteEvidence(
        self,
        evidenceId: str,
        userId: str,
        userRole: str = "",
        userDept: Optional[str] = None
    ) -> Tuple[bool, str]:
        """FR-030 & BR-008: Remove wrongly uploaded evidence before verification with ownership verification."""
        ev = self.evidence_repo.findById(evidenceId)
        if not ev:
            return False, "Evidence file not found."

        activity = self.activity_repo.findById(ev.activityId)
        if not activity:
            return False, "Parent activity not found."

        if activity.status == ActivityStatus.VERIFIED:
            return False, "Evidence cannot be deleted after activity has been verified (BR-008)."

        # Authorization check: only original uploader, assigned staff, authorized coordinator, or admin can delete
        is_uploader = (ev.uploadedBy == userId)
        is_assignee = (activity.assignedTo == userId)
        is_dept_coord = (userRole == Role.DEPARTMENT_COORDINATOR.value and userDept == activity.departmentId)
        is_admin = (userRole in [Role.ADMINISTRATOR.value, Role.IQAC_COORDINATOR.value])

        if not (is_uploader or is_assignee or is_dept_coord or is_admin):
            return False, "Access Denied: You do not have permission to delete this evidence file."

        # Remove from disk
        try:
            self.file_store.remove(ev.filePath)
        except Exception:
            pass

        self.evidence_repo.delete(evidenceId)

        self.history_service.recordChange(
            activityId=activity.activityId,
            userId=userId,
            action="Evidence Deleted",
            oldValue=ev.fileName,
            newValue=f"Removed by {userId}"
        )

        return True, "Evidence file removed successfully."

    def getEvidence(self, evidenceId: str) -> Optional[Evidence]:
        return self.evidence_repo.findById(evidenceId)

    def listEvidence(self, activityId: str) -> List[Evidence]:
        return self.evidence_repo.findByActivityId(activityId)
