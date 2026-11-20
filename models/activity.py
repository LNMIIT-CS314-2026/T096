from datetime import datetime, date
from typing import Optional, List
from models.enums import Priority, ActivityStatus

# Valid status transitions as defined in SRS Section 17 & Section 48.5
VALID_TRANSITIONS = {
    ActivityStatus.PLANNED: [ActivityStatus.ASSIGNED, ActivityStatus.CANCELLED],
    ActivityStatus.ASSIGNED: [ActivityStatus.IN_PROGRESS, ActivityStatus.EVIDENCE_UPLOADED, ActivityStatus.CANCELLED],
    ActivityStatus.IN_PROGRESS: [ActivityStatus.EVIDENCE_UPLOADED, ActivityStatus.COMPLETED, ActivityStatus.SUBMITTED, ActivityStatus.CANCELLED],
    ActivityStatus.EVIDENCE_UPLOADED: [ActivityStatus.COMPLETED, ActivityStatus.SUBMITTED, ActivityStatus.IN_PROGRESS, ActivityStatus.CANCELLED],
    ActivityStatus.COMPLETED: [ActivityStatus.SUBMITTED, ActivityStatus.IN_PROGRESS, ActivityStatus.CANCELLED],
    ActivityStatus.SUBMITTED: [ActivityStatus.VERIFIED, ActivityStatus.RETURNED, ActivityStatus.CANCELLED],
    ActivityStatus.RETURNED: [ActivityStatus.IN_PROGRESS, ActivityStatus.EVIDENCE_UPLOADED, ActivityStatus.CANCELLED],
    ActivityStatus.VERIFIED: [],  # Terminal state (locked)
    ActivityStatus.CANCELLED: []  # Terminal state (locked, BR-012)
}

class Activity:
    """
    Activity entity (SRS Section 35.9 & Section 45.4.9, Table 14 & 15).
    Central class holding lifecycle state, validation, and metadata.
    """
    def __init__(
        self,
        activityId: str,
        title: str,
        deadline: str,
        priority: Priority | str = Priority.MEDIUM,
        status: ActivityStatus | str = ActivityStatus.ASSIGNED,
        outcome: str = "",
        domainId: str = "",
        departmentId: str = "",
        createdBy: str = "",
        assignedTo: Optional[str] = None,
        plannedStart: Optional[str] = None,
        description: str = "",
        createdAt: Optional[str] = None,
        lastUpdatedOn: Optional[str] = None
    ):
        self.activityId = activityId
        self.title = title
        self.deadline = deadline
        self.priority = priority if isinstance(priority, Priority) else Priority(priority)
        self.status = status if isinstance(status, ActivityStatus) else ActivityStatus(status)
        self.outcome = outcome
        self.domainId = domainId
        self.departmentId = departmentId
        self.createdBy = createdBy
        self.assignedTo = assignedTo
        self.plannedStart = plannedStart
        self.description = description
        self.createdAt = createdAt or datetime.now().isoformat()
        self.lastUpdatedOn = lastUpdatedOn or self.createdAt

    def canTransitionTo(self, newStatus: ActivityStatus | str) -> bool:
        target = newStatus if isinstance(newStatus, ActivityStatus) else ActivityStatus(newStatus)
        allowed = VALID_TRANSITIONS.get(self.status, [])
        if target not in allowed:
            return False
        # Submission for verification strictly requires an outcome to be recorded (FR-023, BR-007)
        if target == ActivityStatus.SUBMITTED and (not self.outcome or not self.outcome.strip()):
            return False
        return True

    def updateStatus(self, newStatus: ActivityStatus | str, userId: str = "") -> bool:
        """Validates state transition and updates status (FR-022, BR-007, BR-012)."""
        target = newStatus if isinstance(newStatus, ActivityStatus) else ActivityStatus(newStatus)
        if target == self.status:
            return True
        if not self.canTransitionTo(target):
            return False
        self.status = target
        self.lastUpdatedOn = datetime.now().isoformat()
        return True

    def assign(self, staffId: str) -> None:
        """Assigns activity to a faculty/staff member and sets status to ASSIGNED."""
        self.assignedTo = staffId
        if self.status == ActivityStatus.PLANNED:
            self.status = ActivityStatus.ASSIGNED
        self.lastUpdatedOn = datetime.now().isoformat()

    def recordOutcome(self, outcomeText: str) -> None:
        self.outcome = outcomeText
        self.lastUpdatedOn = datetime.now().isoformat()

    def cancel(self) -> bool:
        if self.status == ActivityStatus.VERIFIED:
            return False
        self.status = ActivityStatus.CANCELLED
        self.lastUpdatedOn = datetime.now().isoformat()
        return True

    def canAcceptEvidence(self) -> bool:
        """Evidence cannot be uploaded if verified or cancelled (BR-008, BR-012)."""
        return self.status not in [ActivityStatus.VERIFIED, ActivityStatus.CANCELLED]

    def getResponsibleEntity(self) -> dict:
        """
        SRS BR-002: Exactly one responsible entity per activity:
        either an assigned individual staff member, or the owning department.
        """
        if self.assignedTo:
            return {"type": "STAFF", "identifier": self.assignedTo, "isStaff": True}
        return {"type": "DEPARTMENT", "identifier": self.departmentId, "isStaff": False}

    def isOverdue(self, now: Optional[datetime] = None) -> bool:
        """
        SRS FR-019, BR-009, Section 48.5:
        Overdue condition applies when deadline has passed (deadline < today)
        and activity is not completed, submitted, verified, or cancelled.
        Crucially: activities RETURNED for rework whose deadline has passed are OVERDUE.
        """
        if not self.deadline or self.status in [ActivityStatus.VERIFIED, ActivityStatus.CANCELLED, ActivityStatus.COMPLETED, ActivityStatus.SUBMITTED]:
            return False
        try:
            deadline_date = datetime.strptime(self.deadline[:10], "%Y-%m-%d").date()
            current_date = now.date() if now else date.today()
            return deadline_date < current_date
        except Exception:
            return False

    def to_dict(self):
        return {
            "activityId": self.activityId,
            "title": self.title,
            "deadline": self.deadline,
            "plannedStart": self.plannedStart,
            "priority": self.priority.value,
            "status": self.status.value,
            "outcome": self.outcome,
            "domainId": self.domainId,
            "departmentId": self.departmentId,
            "createdBy": self.createdBy,
            "assignedTo": self.assignedTo,
            "responsibleEntity": self.getResponsibleEntity(),
            "description": self.description,
            "createdAt": self.createdAt,
            "lastUpdatedOn": self.lastUpdatedOn,
            "isOverdue": self.isOverdue()
        }
