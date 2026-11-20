import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from models.activity import Activity
from models.enums import ActivityStatus, Priority
from repositories.activity_repository import ActivityRepository
from repositories.evidence_repository import EvidenceRepository
from services.notification_service import NotificationService
from services.history_service import HistoryService

class ActivityService:
    """
    Section 47.2.3 Activity Management Service (IActivityAdmin).
    Provides activity operations (create, list, assign, status update, outcome, cancel)
    with strict validation of SRS constraints and persistent history logging.
    """
    def __init__(
        self,
        activity_repo: Optional[ActivityRepository] = None,
        notif_service: Optional[NotificationService] = None,
        history_service: Optional[HistoryService] = None,
        evidence_repo: Optional[EvidenceRepository] = None
    ):
        self.activity_repo = activity_repo or ActivityRepository()
        self.notif_service = notif_service or NotificationService()
        self.history_service = history_service or HistoryService()
        self.evidence_repo = evidence_repo or EvidenceRepository()

    def createActivity(
        self,
        coordinatorId: str,
        details: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[Activity]]:
        title = details.get("title", "").strip()
        deadline = details.get("deadline", "").strip()
        planned_start = details.get("plannedStart", "").strip() or None
        department_id = details.get("departmentId", "").strip()
        domain_id = details.get("domainId", "").strip()
        assignee = details.get("assignedTo")
        assignee = assignee.strip() if assignee else None
        description = details.get("description", "").strip()

        # Character limits & validation
        if not title:
            return False, "Activity title is required.", None
        if len(title) > 150:
            return False, "Activity title cannot exceed 150 characters.", None

        if len(description) > 500:
            return False, "Activity description cannot exceed 500 characters.", None

        if not deadline:
            return False, "Activity deadline is required (BR-003).", None

        if not department_id:
            return False, "Department is required.", None

        # BR-003: Deadline cannot be before planned start date
        if planned_start and deadline:
            try:
                start_dt = datetime.strptime(planned_start[:10], "%Y-%m-%d").date()
                end_dt = datetime.strptime(deadline[:10], "%Y-%m-%d").date()
                if end_dt < start_dt:
                    return False, "Deadline cannot be before the planned start date (BR-003).", None
            except ValueError:
                return False, "Invalid date format. Expected YYYY-MM-DD.", None

        # BR-004: An activity must be tagged to a domain area before it is assigned
        if assignee and not domain_id:
            return False, "An activity must be tagged to a domain area before it is assigned (BR-004).", None

        if assignee:
            from repositories.user_repository import UserRepository as _UR
            from models.enums import Role as _Role
            _ur = _UR()
            _assignee_user = _ur.findById(assignee)
            if not _assignee_user:
                return False, "Assigned user not found.", None
            if _assignee_user.role.value not in [_Role.FACULTY_STAFF.value, _Role.DEPARTMENT_COORDINATOR.value]:
                return False, "Only Faculty/Staff or Department Coordinators can be assigned to activities (BR-002).", None
            if _assignee_user.departmentId and department_id and _assignee_user.departmentId != department_id:
                return False, f"Assignee '{_assignee_user.name}' does not belong to the selected department '{department_id}' (BR-002).", None

        activity_id = f"ACT-{uuid.uuid4().hex[:6].upper()}"

        status = ActivityStatus.ASSIGNED if assignee else ActivityStatus.PLANNED

        activity = Activity(
            activityId=activity_id,
            title=title,
            deadline=deadline,
            priority=details.get("priority", Priority.MEDIUM),
            status=status,
            domainId=domain_id,
            departmentId=department_id,
            createdBy=coordinatorId,
            assignedTo=assignee,
            plannedStart=planned_start,
            description=description
        )
        self.activity_repo.save(activity)

        # Log creation to audit trail (FR-051, Collaboration UC-004 Seq 5)
        self.history_service.recordChange(
            activityId=activity_id,
            userId=coordinatorId,
            action="Created",
            oldValue=None,
            newValue=status.value
        )

        if assignee:
            self.notif_service.notify(
                assignee,
                "ASSIGNMENT",
                f"You have been assigned to activity: '{activity.title}' (Deadline: {activity.deadline})"
            )

        return True, f"Activity {activity_id} created successfully.", activity

    def updateStatus(self, activityId: str, newStatus: ActivityStatus | str, userId: str = "") -> Tuple[bool, str]:
        activity = self.activity_repo.findById(activityId)
        if not activity:
            return False, "Activity not found."

        old_status = activity.status.value
        target_status = newStatus if isinstance(newStatus, ActivityStatus) else ActivityStatus(newStatus)

        # Transitioning to SUBMITTED must follow full verification submission constraints (FR-023, FR-024, BR-007)
        if target_status == ActivityStatus.SUBMITTED:
            return self.submitForVerification(activityId, userId)

        if not activity.updateStatus(target_status, userId):
            return False, f"Invalid status transition from {old_status} to {target_status.value} (FR-022, BR-012)."

        self.activity_repo.save(activity)

        # Audit trail logging
        self.history_service.recordChange(
            activityId=activityId,
            userId=userId or activity.assignedTo or "SYSTEM",
            action="STATUS_UPDATED",
            oldValue=old_status,
            newValue=target_status.value
        )

        return True, f"Status updated to {activity.status.value}."

    def recordOutcome(self, activityId: str, outcome: str, userId: str = "") -> Tuple[bool, str]:
        clean_outcome = outcome.strip()
        if not clean_outcome:
            return False, "Outcome text cannot be empty."
        if len(clean_outcome) > 1000:
            return False, "Outcome text cannot exceed 1000 characters."

        activity = self.activity_repo.findById(activityId)
        if not activity:
            return False, "Activity not found."

        if activity.status == ActivityStatus.VERIFIED:
            return False, "Cannot modify outcome of a verified activity (BR-008)."
        if activity.status == ActivityStatus.CANCELLED:
            return False, "Cannot modify outcome of a cancelled activity (BR-012)."

        self.activity_repo.recordOutcome(activityId, clean_outcome)

        self.history_service.recordChange(
            activityId=activityId,
            userId=userId or activity.assignedTo or "SYSTEM",
            action="OUTCOME_RECORDED",
            oldValue=None,
            newValue=clean_outcome[:80] + ("..." if len(clean_outcome) > 80 else "")
        )

        return True, "Outcome recorded successfully."

    def submitForVerification(self, activityId: str, userId: str) -> Tuple[bool, str]:
        """
        UC-010, FR-024: Submit activity for IQAC verification.
        Requires outcome to be recorded (FR-023) and valid state transition (BR-007).
        """
        activity = self.activity_repo.findById(activityId)
        if not activity:
            return False, "Activity not found."

        if activity.status in [ActivityStatus.VERIFIED, ActivityStatus.CANCELLED]:
            return False, f"Activity is {activity.status.value} and cannot be submitted."

        # FR-023: Outcome must be recorded before submission
        if not activity.outcome or not activity.outcome.strip():
            return False, "An outcome must be recorded before submitting for verification (FR-023). Please fill in the Outcome field first."

        # FR-024, BR-006: At least one supporting evidence document must be uploaded
        evidence_list = self.evidence_repo.findByActivity(activityId)
        if not evidence_list:
            return False, "Cannot submit activity for verification without uploading evidence. At least one supporting document is required."

        # BR-007: Enforce valid state machine transition
        old_status = activity.status.value
        if not activity.canTransitionTo(ActivityStatus.SUBMITTED):
            return False, f"Cannot submit from '{old_status}'. Activity must be In Progress, Evidence Uploaded, Completed, or Returned (BR-007)."

        activity.status = ActivityStatus.SUBMITTED
        from datetime import datetime as _dt
        activity.lastUpdatedOn = _dt.now().isoformat()
        self.activity_repo.save(activity)

        self.history_service.recordChange(
            activityId=activityId,
            userId=userId,
            action="SUBMITTED_FOR_VERIFICATION",
            oldValue=old_status,
            newValue="SUBMITTED"
        )

        # Notify coordinator (FR-044)
        if activity.createdBy:
            self.notif_service.notify(
                activity.createdBy,
                "VERIFICATION",
                f"Activity '{activity.title}' submitted for IQAC verification."
            )

        return True, "Activity submitted for IQAC verification."

    def cancelActivity(self, activityId: str, userId: str, reason: str = "") -> Tuple[bool, str]:
        activity = self.activity_repo.findById(activityId)
        if not activity:
            return False, "Activity not found."

        if activity.status == ActivityStatus.VERIFIED:
            return False, "Cannot cancel an already verified activity (BR-012)."

        old_status = activity.status.value
        if not activity.cancel():
            return False, "Could not cancel activity."

        self.activity_repo.save(activity)

        self.history_service.recordChange(
            activityId=activityId,
            userId=userId,
            action="CANCELLED",
            oldValue=old_status,
            newValue=f"CANCELLED: {reason.strip()}" if reason else "CANCELLED"
        )

        return True, "Activity cancelled successfully."

    def editActivity(self, activityId: str, userId: str, userRole: str, userDept: str, details: dict) -> tuple:
        """FR-009, FR-012: Edit activity title, description, deadline, priority. Coordinator/admin only."""
        from models.enums import Role as _Role
        activity = self.activity_repo.findById(activityId)
        if not activity:
            return False, "Activity not found."
        if activity.status in [ActivityStatus.VERIFIED, ActivityStatus.CANCELLED]:
            return False, f"Cannot edit a {activity.status.value} activity."
        # Authorization
        if userRole == _Role.DEPARTMENT_COORDINATOR.value and activity.departmentId != userDept:
            return False, "You can only edit activities in your own department."
        if userRole not in [_Role.DEPARTMENT_COORDINATOR.value, _Role.IQAC_COORDINATOR.value, _Role.ADMINISTRATOR.value]:
            return False, "Only coordinators or administrators may edit activity details."

        title = details.get("title", "").strip()
        description = details.get("description", "").strip()
        deadline = details.get("deadline", "").strip()
        priority_str = details.get("priority", "").strip()
        planned_start = details.get("planned_start", "").strip() or None
        domain_id = details.get("domain_id", "").strip()

        if title and len(title) > 150:
            return False, "Title cannot exceed 150 characters."
        if description and len(description) > 500:
            return False, "Description cannot exceed 500 characters."

        # Validate domain / criterion (BR-001)
        if domain_id:
            from repositories.department_repository import DomainAreaRepository
            dm = DomainAreaRepository().findById(domain_id)
            if not dm:
                return False, f"Quality criterion '{domain_id}' does not exist (BR-001)."

        # BR-003 deadline check
        if planned_start and deadline:
            try:
                from datetime import datetime as _dt
                s = _dt.strptime(planned_start[:10], "%Y-%m-%d").date()
                e = _dt.strptime(deadline[:10], "%Y-%m-%d").date()
                if e < s:
                    return False, "Deadline cannot be before planned start date (BR-003)."
            except ValueError:
                return False, "Invalid date format."

        old_title = activity.title
        old_deadline = activity.deadline
        old_domain = activity.domainId

        if title:
            activity.title = title
        if description:
            activity.description = description
        if deadline:
            activity.deadline = deadline
        if domain_id:
            activity.domainId = domain_id
        if planned_start is not None:
            activity.plannedStart = planned_start
        if priority_str:
            from models.enums import Priority as _P
            try:
                activity.priority = _P(priority_str)
            except ValueError:
                pass
        from datetime import datetime as _dt2
        activity.lastUpdatedOn = _dt2.now().isoformat()
        self.activity_repo.save(activity)

        # Audit trail logging for edits
        self.history_service.recordChange(
            activityId=activityId,
            userId=userId,
            action="EDITED",
            oldValue=old_title,
            newValue=f"title={activity.title}, deadline={activity.deadline}, domain={activity.domainId}"
        )

        if old_deadline != activity.deadline:
            self.history_service.recordChange(
                activityId=activityId,
                userId=userId,
                action="DEADLINE_MODIFIED",
                oldValue=old_deadline,
                newValue=activity.deadline
            )
            # Notify assignee of revised deadline (FR-012, FR-041)
            if activity.assignedTo:
                self.notif_service.notify(
                    activity.assignedTo,
                    "DEADLINE_MODIFIED",
                    f"Deadline for activity '{activity.title}' ({activityId}) updated to {activity.deadline}."
                )

        if old_domain != activity.domainId:
            self.history_service.recordChange(
                activityId=activityId,
                userId=userId,
                action="CRITERION_CHANGED",
                oldValue=old_domain,
                newValue=activity.domainId
            )
        return True, "Activity updated successfully."

    def reassignActivity(self, activityId: str, requesterId: str, requesterRole: str, requesterDept: str, newAssigneeId: str) -> tuple:
        """FR-011: Reassign an activity to a different staff member."""
        from models.enums import Role as _Role
        from repositories.user_repository import UserRepository as _UR
        activity = self.activity_repo.findById(activityId)
        if not activity:
            return False, "Activity not found."
        if activity.status in [ActivityStatus.VERIFIED, ActivityStatus.CANCELLED]:
            return False, f"Cannot reassign a {activity.status.value} activity."
        if requesterRole == _Role.DEPARTMENT_COORDINATOR.value and activity.departmentId != requesterDept:
            return False, "You can only reassign activities in your own department."
        if requesterRole not in [_Role.DEPARTMENT_COORDINATOR.value, _Role.IQAC_COORDINATOR.value, _Role.ADMINISTRATOR.value]:
            return False, "Only coordinators or administrators may reassign activities."

        _ur = _UR()
        new_assignee = _ur.findById(newAssigneeId)
        if not new_assignee:
            return False, "New assignee user not found."
        if new_assignee.role.value not in [_Role.FACULTY_STAFF.value, _Role.DEPARTMENT_COORDINATOR.value]:
            return False, "Only Faculty/Staff or Department Coordinators can be assigned to activities (BR-002)."
        if new_assignee.departmentId and activity.departmentId and new_assignee.departmentId != activity.departmentId:
            return False, f"New assignee does not belong to the activity's department '{activity.departmentId}' (BR-002)."

        old_assignee = activity.assignedTo
        activity.assignedTo = newAssigneeId
        if activity.status == ActivityStatus.PLANNED:
            activity.status = ActivityStatus.ASSIGNED
        from datetime import datetime as _dt
        activity.lastUpdatedOn = _dt.now().isoformat()
        self.activity_repo.save(activity)
        self.history_service.recordChange(
            activityId=activityId,
            userId=requesterId,
            action="REASSIGNED",
            oldValue=old_assignee or "Unassigned",
            newValue=newAssigneeId
        )
        self.notif_service.notify(
            newAssigneeId,
            "ASSIGNMENT",
            f"You have been assigned to activity: '{activity.title}' ({activityId}) (Deadline: {activity.deadline})"
        )
        if old_assignee and old_assignee != newAssigneeId:
            self.notif_service.notify(
                old_assignee,
                "ASSIGNMENT",
                f"You have been removed from activity: '{activity.title}' ({activityId}). A new person has been assigned."
            )
        return True, f"Activity reassigned to {new_assignee.name} successfully."

    def updateStatusByUser(self, activityId: str, newStatus: str, userId: str, userRole: str, userDept: str, remarks: str = "") -> tuple:
        """FR-020, FR-021: Faculty/Staff can update progress status and add remarks."""
        from models.enums import Role as _Role
        activity = self.activity_repo.findById(activityId)
        if not activity:
            return False, "Activity not found."

        # Authorization: only assigned user or dept coordinator or admin
        is_authorized = (
            activity.assignedTo == userId
            or (userRole == _Role.DEPARTMENT_COORDINATOR.value and activity.departmentId == userDept)
            or userRole in [_Role.IQAC_COORDINATOR.value, _Role.ADMINISTRATOR.value]
        )
        if not is_authorized:
            return False, "You are not authorized to update this activity's status."

        # Staff can only move to allowed user-facing statuses
        USER_ALLOWED_STATUSES = ["IN_PROGRESS", "EVIDENCE_UPLOADED", "COMPLETED"]
        if userRole == _Role.FACULTY_STAFF.value and newStatus not in USER_ALLOWED_STATUSES:
            return False, f"Faculty/Staff can only update status to: {', '.join(USER_ALLOWED_STATUSES)}."

        success, message = self.updateStatus(activityId, newStatus, userId)
        if not success:
            return False, message

        # Save progress remarks if provided
        if remarks.strip():
            if len(remarks.strip()) > 500:
                return False, "Remarks cannot exceed 500 characters."
            self.history_service.recordChange(
                activityId=activityId,
                userId=userId,
                action="PROGRESS_REMARK",
                oldValue=None,
                newValue=remarks.strip()[:200]
            )
        return True, message

    def listActivities(
        self,
        status: Optional[str] = None,
        departmentId: Optional[str] = None,
        assigneeId: Optional[str] = None
    ) -> List[Activity]:
        if assigneeId:
            acts = self.activity_repo.findByAssignee(assigneeId)
            if status and status != "All":
                acts = [a for a in acts if a.status.value == status]
            return acts
        return self.activity_repo.findAll(status=status, departmentId=departmentId)

    def getActivity(self, activityId: str) -> Optional[Activity]:
        return self.activity_repo.findById(activityId)

    def getDashboardCounts(
        self,
        role: Optional[str] = None,
        departmentId: Optional[str] = None,
        userId: Optional[str] = None
    ) -> Optional[Dict[str, int]]:
        """Role- and department-aware dashboard KPI metrics (FR-050)."""
        return self.activity_repo.getDashboardCounts(role=role, departmentId=departmentId, userId=userId)
