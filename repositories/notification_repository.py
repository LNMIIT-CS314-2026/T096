from typing import List
from models.notification import Notification
from repositories.database import get_db_connection

class NotificationRepository:
    def save(self, notif: Notification) -> None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO notifications (notification_id, recipient, message, notification_type, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(notification_id) DO UPDATE SET
                message = excluded.message
            """,
            (notif.notificationId, notif.recipient, notif.message, notif.notificationType, notif.createdAt)
        )
        conn.commit()
        conn.close()

    def findByRecipient(self, recipient: str, limit: int = 20) -> List[Notification]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM notifications WHERE recipient = ? ORDER BY created_at DESC LIMIT ?",
            (recipient, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        return [
            Notification(
                notificationId=r["notification_id"],
                recipient=r["recipient"],
                message=r["message"],
                notificationType=r["notification_type"],
                createdAt=r["created_at"]
            )
            for r in rows
        ]

    def hasNotificationToday(self, recipient: str, notificationType: str, identifier: str, date_prefix: str) -> bool:
        """Checks if a notification containing the identifier has already been dispatched today (C-24 deduplication)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 1 FROM notifications 
            WHERE recipient = ? AND notification_type = ? AND message LIKE ? AND created_at LIKE ?
            LIMIT 1
            """,
            (recipient, notificationType, f"%{identifier}%", f"{date_prefix}%")
        )
        row = cursor.fetchone()
        conn.close()
        return row is not None
