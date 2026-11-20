from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from routes.auth_routes import login_required, roles_required
from services.verification_service import VerificationService
from services.evidence_service import EvidenceService
from repositories.user_repository import UserRepository
from models.enums import Role

verification_bp = Blueprint("verification", __name__)
verification_service = VerificationService()
evidence_service = EvidenceService()
user_repo = UserRepository()

@verification_bp.route("/verification")
@login_required
@roles_required(Role.IQAC_MEMBER, Role.IQAC_COORDINATOR)
def verification_queue():
    queue = verification_service.getQueue()
    return render_template("verification_queue.html", queue=queue)

@verification_bp.route("/verification/<activity_id>/review")
@login_required
@roles_required(Role.IQAC_MEMBER, Role.IQAC_COORDINATOR)
def review_activity(activity_id):
    from services.activity_service import ActivityService
    act = ActivityService().getActivity(activity_id)
    if not act:
        flash("Activity not found.", "danger")
        return redirect(url_for("verification.verification_queue"))

    evidence_list = evidence_service.listEvidence(activity_id)
    assignee = user_repo.findById(act.assignedTo) if act.assignedTo else None

    return render_template(
        "review_activity.html",
        activity=act,
        evidence_list=evidence_list,
        assignee_name=assignee.name if assignee else "Unassigned"
    )

@verification_bp.route("/verification/<activity_id>/decide", methods=["POST"])
@login_required
@roles_required(Role.IQAC_MEMBER, Role.IQAC_COORDINATOR)
def decide_verification(activity_id):
    action = request.form.get("action")
    comments = request.form.get("comments", "").strip()
    member_id = session.get("user_id")

    if action == "verify":
        success, message, _ = verification_service.verify(activity_id, member_id, comments)
    elif action == "return":
        success, message, _ = verification_service.returnActivity(activity_id, member_id, comments)
    else:
        flash("Invalid verification action specified.", "danger")
        return redirect(url_for("verification.verification_queue"))

    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for("verification.verification_queue"))
