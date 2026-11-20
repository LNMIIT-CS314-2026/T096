import sqlite3
from typing import List, Optional
from datetime import datetime
from models.history_log import ActivityHistoryLog
from repositories.database import get_db_connection

class HistoryRepository:
    """
    Persistence operations for ActivityHistoryLog (SRS Table 16, Table 27).
    """
    def save(self, log_entry: ActivityHistoryLog) -> None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO activity_history_log (
                log_id, activity_id, performed_by, action, old_value, new_value, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(log_id) DO UPDATE SET
                action = excluded.action,
                old_value = excluded.old_value,
                new_value = excluded.new_value,
                timestamp = excluded.timestamp
            """,
            (
                log_entry.logId,
                log_entry.activityId,
                log_entry.performedBy,
                log_entry.action,
                log_entry.oldValue,
                log_entry.newValue,
                log_entry.timestamp
            )
        )
        conn.commit()
        conn.close()

    def findByActivityId(self, activityId: str) -> List[ActivityHistoryLog]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM activity_history_log
            WHERE activity_id = ?
            ORDER BY timestamp ASC
            """,
            (activityId,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [
            ActivityHistoryLog(
                logId=r["log_id"],
                activityId=r["activity_id"],
                performedBy=r["performed_by"],
                action=r["action"],
                oldValue=r["old_value"],
                newValue=r["new_value"],
                timestamp=r["timestamp"]
            )
            for r in rows
        ]
