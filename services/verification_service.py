import uuid
from typing import Optional, List, Tuple
from models.verification import Verification
from models.activity import Activity
from models.enums import ActivityStatus, VerificationStatus, Decision
from repositories.verification_repository import VerificationRepository
from repositories.activity_repository import ActivityRepository
from repositories.evidence_repository import EvidenceRepository
from services.notification_service import NotificationService
from services.history_service import HistoryService

class VerificationService:
    """
    Section 47.2.5 Verification Service (IVerify) & Section 48.4 (UC-011).
    Reviews submissions, executes verify/return decisions, locks evidence,
    prevents self-verification (C-13), and maintains full audit trail (FR-031 - FR-035, BR-006 - BR-008).
    """
    def __init__(
        self,
        verification_repo: Optional[VerificationRepository] = None,
        activity_repo: Optional[ActivityRepository] = None,
        evidence_repo: Optional[EvidenceRepository] = None,
        notif_service: Optional[NotificationService] = None,
        history_service: Optional[HistoryService] = None
    ):
        self.verification_repo = verification_repo or VerificationRepository()
        self.activity_repo = activity_repo or ActivityRepository()
        self.evidence_repo = evidence_repo or EvidenceRepository()
        self.notif_service = notif_service or NotificationService()
        self.history_service = history_service or HistoryService()

    def getQueue(self) -> List[Activity]:
        """
        FR-031: Returns only SUBMITTED activities awaiting IQAC verification.
        Activities must be formally submitted (FR-024) before they can be reviewed.
        EVIDENCE_UPLOADED alone is NOT sufficient — submission is a required step.
        """
        all_acts = self.activity_repo.findAll()
        return [a for a in all_acts if a.status == ActivityStatus.SUBMITTED]

    def verify(self, activityId: str, memberId: str, comments: str = "") -> Tuple[bool, str, Optional[Verification]]:
        activity = self.activity_repo.findById(activityId)
        if not activity:
            return False, "Activity not found.", None

        # Conflict of Interest Protection (C-13: No self-verification)
        if activity.assignedTo == memberId or activity.createdBy == memberId:
            return False, "Conflict of Interest: Verifier cannot review or approve an activity assigned to or created by themselves (Rule C-13: No self-verification).", None

        if activity.status != ActivityStatus.SUBMITTED:
            return False, f"Activity must be in SUBMITTED status for IQAC review (currently: {activity.status.value}). Please submit the activity first (FR-024).", None

        evidence_list = self.evidence_repo.findByActivityId(activityId)
        if not evidence_list:
            return False, "No evidence submitted. Cannot verify activity without supporting documents.", None

        clean_comments = comments.strip()
        if len(clean_comments) > 500:
            return False, "Verification comments cannot exceed 500 characters.", None

        ver_id = f"VER-{uuid.uuid4().hex[:6].upper()}"
        ver = Verification(
            verificationId=ver_id,
            activityId=activityId,
            verifiedBy=memberId,
            decision=Decision.APPROVED,
            comments=clean_comments or "Verified and approved by IQAC"
        )
        self.verification_repo.save(ver)

        # Update activity to VERIFIED & lock evidence (BR-006, BR-008)
        old_status = activity.status.value
        activity.status = ActivityStatus.VERIFIED
        self.activity_repo.save(activity)
        self.evidence_repo.updateStatusByActivityId(activityId, VerificationStatus.VERIFIED)

        # Record decision in activity history log (Collaboration UC-011 Seq 5)
        self.history_service.recordChange(
            activityId=activityId,
            userId=memberId,
            action="VERIFIED",
            oldValue=old_status,
            newValue="VERIFIED (Approved)"
        )

        # Notify responsible user and department coordinator (FR-044)
        if activity.assignedTo:
            self.notif_service.notify(
                activity.assignedTo,
                "VERIFICATION",
                f"Activity '{activity.title}' has been successfully verified and approved by IQAC."
            )
        if activity.createdBy and activity.createdBy != activity.assignedTo:
            self.notif_service.notify(
                activity.createdBy,
                "VERIFICATION",
                f"Activity '{activity.title}' has been verified and approved by IQAC."
            )

        return True, "Activity verified. Status = Verified. Responsible user and coordinator notified.", ver

    def returnActivity(self, activityId: str, memberId: str, reason: str) -> Tuple[bool, str, Optional[Verification]]:
        clean_reason = reason.strip()
        if not clean_reason:
            return False, "Reason is required to return an activity for rework (FR-034).", None

        if len(clean_reason) > 500:
            return False, "Return reason cannot exceed 500 characters.", None

        activity = self.activity_repo.findById(activityId)
        if not activity:
            return False, "Activity not found.", None

        # Conflict of Interest Protection (C-13: No self-verification)
        if activity.assignedTo == memberId or activity.createdBy == memberId:
            return False, "Conflict of Interest: Verifier cannot return their own activity (Rule C-13: No self-verification).", None

        if activity.status != ActivityStatus.SUBMITTED:
            return False, f"Activity must be in SUBMITTED status for IQAC review (currently: {activity.status.value}). Please submit the activity first (FR-024).", None

        ver_id = f"VER-{uuid.uuid4().hex[:6].upper()}"
        ver = Verification(
            verificationId=ver_id,
            activityId=activityId,
            verifiedBy=memberId,
            decision=Decision.RETURNED_FOR_CORRECTION,
            comments=clean_reason
        )
        self.verification_repo.save(ver)

        old_status = activity.status.value
        activity.status = ActivityStatus.RETURNED
        self.activity_repo.save(activity)
        self.evidence_repo.updateStatusByActivityId(activityId, VerificationStatus.RETURNED)

        # Record decision in activity history log (BR-007)
        self.history_service.recordChange(
            activityId=activityId,
            userId=memberId,
            action="RETURNED",
            oldValue=old_status,
            newValue=f"RETURNED: {clean_reason}"
        )

        # Notify responsible user and coordinator
        if activity.assignedTo:
            self.notif_service.notify(
                activity.assignedTo,
                "RETURN",
                f"Activity '{activity.title}' returned for rework: {clean_reason}"
            )
        if activity.createdBy and activity.createdBy != activity.assignedTo:
            self.notif_service.notify(
                activity.createdBy,
                "RETURN",
                f"Activity '{activity.title}' was returned for correction: {clean_reason}"
            )

        return True, "Activity returned. Status = Returned. Responsible user notified with your reason.", ver
