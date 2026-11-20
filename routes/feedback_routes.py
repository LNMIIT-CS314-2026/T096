from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from routes.auth_routes import login_required, roles_required
from models.enums import Role
from services.feedback_service import FeedbackService
from repositories.activity_repository import ActivityRepository

feedback_bp = Blueprint("feedback", __name__)
feedback_service = FeedbackService()
activity_repo = ActivityRepository()

@feedback_bp.route("/feedback")
@login_required
def list_feedback_forms():
    """FR-038, UC-019: View available feedback forms."""
    user_id = session.get("user_id")
    user_role = session.get("role")

    forms_with_status = feedback_service.listFormsForUser(user_id)

    return render_template(
        "feedback_list.html",
        forms_with_status=forms_with_status,
        user_role=user_role
    )

@feedback_bp.route("/feedback/<form_id>/submit", methods=["POST"])
@login_required
@roles_required(Role.STUDENT)
def submit_feedback(form_id):
    """FR-038, FR-039, BR-011, UC-019: Only Students are permitted to submit feedback responses."""
    user_id = session.get("user_id")
    user_role = session.get("role")

    rating_val = request.form.get("rating", "5")
    try:
        rating = int(rating_val)
    except ValueError:
        rating = 5

    comments = request.form.get("comments", "").strip()

    success, message = feedback_service.submitResponse(
        formId=form_id,
        userId=user_id,
        userRole=user_role,
        rating=rating,
        comments=comments
    )

    if success:
        flash(message, "success")
    else:
        flash(message, "danger" if "Restricted" in message or "exceed" in message else "warning")

    return redirect(url_for("feedback.list_feedback_forms"))

@feedback_bp.route("/feedback/create", methods=["GET", "POST"])
@login_required
@roles_required(Role.IQAC_COORDINATOR, Role.ADMINISTRATOR)
def create_feedback_form():
    """FR-036, UC-018: Authorised coordinator creates feedback form linked to an activity."""
    activities = activity_repo.findAll()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        activity_id = request.form.get("activity_id", "").strip()
        user_id = session.get("user_id")
        user_role = session.get("role")

        success, message, _ = feedback_service.createForm(
            title=title,
            activityId=activity_id,
            createdBy=user_id,
            creatorRole=user_role,
            opensAt=request.form.get("opens_at", "").strip() or None,
            closesAt=request.form.get("closes_at", "").strip() or None
        )

        if success:
            flash(message, "success")
            return redirect(url_for("feedback.list_feedback_forms"))
        else:
            flash(message, "danger")
            return render_template("feedback_create.html", activities=activities)

    return render_template("feedback_create.html", activities=activities)

@feedback_bp.route("/feedback/<form_id>/summary")
@login_required
@roles_required(Role.FACULTY_STAFF, Role.DEPARTMENT_COORDINATOR, Role.IQAC_MEMBER, Role.IQAC_COORDINATOR, Role.ADMINISTRATOR)
def feedback_summary(form_id):
    """FR-040: View summary of collected feedback responses."""
    user_role = session.get("role")
    success, message, data = feedback_service.getSummary(form_id, user_role)

    if not success or not data:
        flash(message, "danger")
        return redirect(url_for("feedback.list_feedback_forms"))

    return render_template(
        "feedback_summary.html",
        form=data["form"],
        responses=data["responses"],
        avg_rating=data["avg_rating"]
    )
