from datetime import datetime
from typing import Optional
from models.enums import Decision

class Verification:
    """Verification entity (Section 45.4.12)."""
    def __init__(
        self,
        verificationId: str,
        activityId: str,
        verifiedBy: str,
        decision: Decision | str,
        comments: str = "",
        decisionDate: Optional[str] = None
    ):
        self.verificationId = verificationId
        self.activityId = activityId
        self.verifiedBy = verifiedBy
        self.decision = decision if isinstance(decision, Decision) else Decision(decision)
        self.comments = comments
        self.decisionDate = decisionDate or datetime.now().isoformat()

    def to_dict(self):
        return {
            "verificationId": self.verificationId,
            "activityId": self.activityId,
            "verifiedBy": self.verifiedBy,
            "decision": self.decision.value,
            "comments": self.comments,
            "decisionDate": self.decisionDate
        }
