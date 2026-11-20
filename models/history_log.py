from datetime import datetime
from typing import Optional

class ActivityHistoryLog:
    """
    Maintains an audit trail of every change made to an activity (who, what, when)
    as specified in SRS Section 35.12 & Section 45.4.10 (Table 16 & Table 17).
    """
    def __init__(
        self,
        logId: str,
        activityId: str,
        performedBy: str,
        action: str,
        oldValue: Optional[str] = None,
        newValue: Optional[str] = None,
        timestamp: Optional[str] = None
    ):
        self._logId = logId
        self._activityId = activityId
        self._performedBy = performedBy
        self._action = action
        self._oldValue = oldValue
        self._newValue = newValue
        self._timestamp = timestamp or datetime.now().isoformat()

    @property
    def logId(self) -> str:
        return self._logId

    @property
    def activityId(self) -> str:
        return self._activityId

    @property
    def performedBy(self) -> str:
        return self._performedBy

    @property
    def action(self) -> str:
        return self._action

    @property
    def oldValue(self) -> Optional[str]:
        return self._oldValue

    @property
    def newValue(self) -> Optional[str]:
        return self._newValue

    @property
    def timestamp(self) -> str:
        return self._timestamp

    def to_dict(self):
        return {
            "logId": self._logId,
            "activityId": self._activityId,
            "performedBy": self._performedBy,
            "action": self._action,
            "oldValue": self._oldValue,
            "newValue": self._newValue,
            "timestamp": self._timestamp
        }
