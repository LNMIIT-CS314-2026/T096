import uuid
from datetime import datetime
from typing import Optional, List
from models.history_log import ActivityHistoryLog
from repositories.history_repository import HistoryRepository

class HistoryService:
    """
    Section 47.2.6 & Section 48.1 History Support (IHistoryLog).
    Maintains persistent audit trail of significant activity events (FR-051, FR-052).
    """
    def __init__(self, history_repo: Optional[HistoryRepository] = None):
        self.history_repo = history_repo or HistoryRepository()

    def recordChange(
        self,
        activityId: str,
        userId: str,
        action: str,
        oldValue: Optional[str] = None,
        newValue: Optional[str] = None
    ) -> ActivityHistoryLog:
        log_id = f"LOG-{uuid.uuid4().hex[:6].upper()}"
        entry = ActivityHistoryLog(
            logId=log_id,
            activityId=activityId,
            performedBy=userId,
            action=action,
            oldValue=oldValue,
            newValue=newValue,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self.history_repo.save(entry)
        return entry

    def getActivityHistory(self, activityId: str) -> List[ActivityHistoryLog]:
        return self.history_repo.findByActivityId(activityId)
