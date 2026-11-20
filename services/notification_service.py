import uuid
from datetime import datetime, date
from typing import List, Optional
from models.notification import Notification
from models.enums import ActivityStatus, Role, NotificationType
from repositories.notification_repository import NotificationRepository
from repositories.user_repository import UserRepository
from repositories.activity_repository import ActivityRepository
from utils.email_sender import EmailSender

class NotificationService:
    """
    Section 47.2.6 NotificationService (INotify).
    Dispatches in-app notifications and Google SMTP alert emails at surface level.
    """
    def __init__(
        self,
        notif_repo: Optional[NotificationRepository] = None,
        user_repo: Optional[UserRepository] = None,
        activity_repo: Optional[ActivityRepository] = None
    ):
        self.notif_repo = notif_repo or NotificationRepository()
        self.user_repo = user_repo or UserRepository()
        self.activity_repo = activity_repo or ActivityRepository()

    def notify(self, userId: str, notificationType: str, message: str) -> bool:
        notif_id = f"NOTIF-{uuid.uuid4().hex[:6].upper()}"
        notif = Notification(
            notificationId=notif_id,
            recipient=userId,
            message=message,
            notificationType=notificationType
        )
        self.notif_repo.save(notif)

        # Send email alert via Google SMTP if email available
        user = self.user_repo.findById(userId) or self.user_repo.findByEmail(userId)
        if user and user.email:
            EmailSender.send_notification_email(user.email, notificationType, message)

        return True

    def getNotifications(self, userId: str) -> List[Notification]:
        return self.notif_repo.findByRecipient(userId)

    def processDeadlineRemindersAndOverdue(self) -> dict:
        """
        SRS FR-042, FR-043 & UC-014:
        Automated scan for:
        1. Approaching deadlines: sends DEADLINE_REMINDER to assignee if deadline is within 3 days.
        2. Overdue activities: sends OVERDUE alert to assignee and department coordinator.
        Deduplicates via C-24 so reminders are not sent multiple times per day.
        """
        today = date.today()
        today_str = today.isoformat()
        dispatched_reminders = 0
        dispatched_overdue = 0

        activities = self.activity_repo.findAll()
        for act in activities:
            if not act.deadline:
                continue

            try:
                deadline_dt = datetime.strptime(act.deadline[:10], "%Y-%m-%d").date()
            except Exception:
                continue

            days_remaining = (deadline_dt - today).days

            # 1. Check for 3-day reminder (FR-042)
            if 0 <= days_remaining <= 3 and act.status not in [ActivityStatus.VERIFIED, ActivityStatus.CANCELLED, ActivityStatus.COMPLETED, ActivityStatus.SUBMITTED]:
                if act.assignedTo:
                    if not self.notif_repo.hasNotificationToday(act.assignedTo, NotificationType.DEADLINE_REMINDER.value, act.activityId, today_str):
                        self.notify(
                            act.assignedTo,
                            NotificationType.DEADLINE_REMINDER.value,
                            f"Reminder: Activity '{act.title}' ({act.activityId}) is due in {days_remaining} day(s) on {act.deadline}."
                        )
                        dispatched_reminders += 1

            # 2. Check for Overdue alert (FR-043, BR-009)
            if act.isOverdue(datetime.now()):
                # Notify assignee
                if act.assignedTo:
                    if not self.notif_repo.hasNotificationToday(act.assignedTo, NotificationType.OVERDUE.value, act.activityId, today_str):
                        self.notify(
                            act.assignedTo,
                            NotificationType.OVERDUE.value,
                            f"Alert: Activity '{act.title}' ({act.activityId}) is OVERDUE (Deadline was {act.deadline})."
                        )
                        dispatched_overdue += 1
                
                # Notify department coordinator
                if act.departmentId:
                    dept_coords = self.user_repo.findAll(departmentId=act.departmentId, role=Role.DEPARTMENT_COORDINATOR.value)
                    for coord in dept_coords:
                        if not self.notif_repo.hasNotificationToday(coord.userId, NotificationType.OVERDUE.value, act.activityId, today_str):
                            self.notify(
                                coord.userId,
                                NotificationType.OVERDUE.value,
                                f"Department Alert: Activity '{act.title}' ({act.activityId}) in your department is OVERDUE."
                            )
                            dispatched_overdue += 1

        return {
            "reminders_sent": dispatched_reminders,
            "overdue_alerts_sent": dispatched_overdue
        }

import threading
import time

_scheduler_running = False
_scheduler_thread = None

def start_background_notification_scheduler(interval_seconds: int = 3600):
    """
    Independent background daemon scheduler for automated deadline reminders
    and overdue activity scans (FR-042, FR-043, UC-014).
    Runs independently of HTTP requests or dashboard page visits.
    """
    global _scheduler_running, _scheduler_thread
    if _scheduler_running:
        return
    _scheduler_running = True

    def _daemon_loop():
        service = NotificationService()
        while _scheduler_running:
            try:
                service.processDeadlineRemindersAndOverdue()
            except Exception as e:
                print(f"[Scheduler Warning] Background notification scan: {e}")
            time.sleep(interval_seconds)

    _scheduler_thread = threading.Thread(target=_daemon_loop, daemon=True, name="NotificationDaemonThread")
    _scheduler_thread.start()

if __name__ == "__main__":
    import sys
    print("Running independent scheduled deadline reminder and overdue notification scanner (FR-042, FR-043)...")
    res = NotificationService().processDeadlineRemindersAndOverdue()
    print(f"Scan complete: {res['reminders_sent']} reminders sent, {res['overdue_alerts_sent']} overdue alerts dispatched.")
    sys.exit(0)
