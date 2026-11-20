from datetime import datetime
from typing import Optional
from models.enums import NotificationType

class Notification:
    """Notification entity (Section 45.4.13)."""
    def __init__(
        self,
        notificationId: str,
        recipient: str,
        message: str,
        notificationType: str = "GENERAL",
        createdAt: Optional[str] = None
    ):
        self.notificationId = notificationId
        self.recipient = recipient
        self.message = message
        self.notificationType = notificationType
        self.createdAt = createdAt or datetime.now().isoformat()

    def to_dict(self):
        return {
            "notificationId": self.notificationId,
            "recipient": self.recipient,
            "message": self.message,
            "notificationType": self.notificationType,
            "createdAt": self.createdAt
        }
