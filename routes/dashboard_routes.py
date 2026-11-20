from flask import Blueprint, render_template, session, redirect, url_for
from routes.auth_routes import login_required
from services.profile_service import ProfileService
from services.activity_service import ActivityService
from repositories.activity_repository import ActivityRepository
from repositories.notification_repository import NotificationRepository
from repositories.department_repository import DepartmentRepository

dashboard_bp = Blueprint("dashboard", __name__)
profile_service = ProfileService()
activity_service = ActivityService()
activity_repo = ActivityRepository()
notif_repo = NotificationRepository()
dept_repo = DepartmentRepository()

@dashboard_bp.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard_view"))
    return redirect(url_for("auth.login"))

@dashboard_bp.route("/dashboard")
@login_required
def dashboard_view():
    user_id = session.get("user_id")
    success, message, data = profile_service.getProfile(user_id)
    if not success or not data:
        return redirect(url_for("auth.logout"))

    user = data["user"]
    department = data["department"]

    from models.enums import Role as _Role
    user_role = session.get("role")
    user_dept = session.get("department_id")

    available_feedback_forms = []

    # Role-scoped counts & activities:
    # - IQAC / Admin: institution-wide KPI counts & recent activities
    # - Department Coordinator: department-scoped KPI counts & department activities
    # - Faculty/Staff: assigned activity KPI counts & assigned activities
    # - Student: strictly no activities visible on dashboard (feedback portal only)
    counts = activity_service.getDashboardCounts(role=user_role, departmentId=user_dept, userId=user_id)

    if user_role in [_Role.IQAC_COORDINATOR.value, _Role.IQAC_MEMBER.value, _Role.ADMINISTRATOR.value]:
        recent_activities = activity_repo.findAll()[:6]
    elif user_role == _Role.DEPARTMENT_COORDINATOR.value:
        recent_activities = activity_repo.findAll(departmentId=user_dept)[:6]
    elif user_role == _Role.FACULTY_STAFF.value:
        recent_activities = activity_repo.findByAssignee(user_id)[:6]
    else:
        # STUDENT: strictly no activities visible on dashboard
        recent_activities = []
        from services.feedback_service import FeedbackService
        available_feedback_forms = FeedbackService().listFormsForUser(user_id)[:6]

    notifications = notif_repo.findByRecipient(user_id, limit=6)

    return render_template(
        "dashboard.html",
        user=user,
        department=department,
        counts=counts,
        recent_activities=recent_activities,
        notifications=notifications,
        available_feedback_forms=available_feedback_forms
    )
