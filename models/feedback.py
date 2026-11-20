from datetime import datetime
from typing import Optional

class FeedbackForm:
    """
    FeedbackForm entity as defined in SRS Section 16 & Section 13.7 (FR-036 - FR-040).
    Includes opens_at / closes_at date window so submissions are only accepted
    within the defined collection window (FR-037, BR-011).
    """
    def __init__(
        self,
        formId: str,
        title: str,
        activityId: str,
        targetRole: str = "STUDENT",
        isOpen: bool = True,
        createdBy: str = "",
        createdAt: Optional[str] = None,
        opensAt: Optional[str] = None,
        closesAt: Optional[str] = None
    ):
        self.formId = formId
        self.title = title
        self.activityId = activityId
        self.targetRole = targetRole
        self._is_open = isOpen
        self.createdBy = createdBy
        self.createdAt = createdAt or datetime.now().isoformat()
        self.opensAt = opensAt       # ISO date string YYYY-MM-DD
        self.closesAt = closesAt     # ISO date string YYYY-MM-DD

    @property
    def isOpen(self) -> bool:
        """A form is open only when _is_open=True AND today falls within [opensAt, closesAt]."""
        if not self._is_open:
            return False
        today = datetime.now().date()
        if self.opensAt:
            try:
                if today < datetime.strptime(self.opensAt[:10], "%Y-%m-%d").date():
                    return False
            except ValueError:
                pass
        if self.closesAt:
            try:
                if today > datetime.strptime(self.closesAt[:10], "%Y-%m-%d").date():
                    return False
            except ValueError:
                pass
        return True

    @isOpen.setter
    def isOpen(self, val: bool):
        self._is_open = bool(val)

    def isAcceptingSubmissions(self) -> bool:
        """Check whether submissions can currently be accepted based on isOpen and date window."""
        return self.isOpen

    def to_dict(self):
        return {
            "formId": self.formId,
            "title": self.title,
            "activityId": self.activityId,
            "targetRole": self.targetRole,
            "isOpen": self.isOpen,
            "opensAt": self.opensAt,
            "closesAt": self.closesAt,
            "createdBy": self.createdBy,
            "createdAt": self.createdAt
        }


class FeedbackResponse:
    """
    FeedbackResponse entity holding student evaluation responses (FR-038, FR-039).
    """
    def __init__(
        self,
        responseId: str,
        formId: str,
        userId: str,
        rating: int,
        comments: str = "",
        submittedAt: Optional[str] = None
    ):
        self.responseId = responseId
        self.formId = formId
        self.userId = userId
        self.rating = rating
        self.comments = comments
        self.submittedAt = submittedAt or datetime.now().isoformat()

    def to_dict(self):
        return {
            "responseId": self.responseId,
            "formId": self.formId,
            "userId": self.userId,
            "rating": self.rating,
            "comments": self.comments,
            "submittedAt": self.submittedAt
        }
