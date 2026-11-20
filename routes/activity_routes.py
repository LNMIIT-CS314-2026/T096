from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file
from routes.auth_routes import login_required, roles_required
from services.activity_service import ActivityService
from services.evidence_service import EvidenceService
from services.history_service import HistoryService
from repositories.department_repository import DepartmentRepository, DomainAreaRepository
from repositories.user_repository import UserRepository
from models.enums import Role, Priority, ActivityStatus

activity_bp = Blueprint("activity", __name__)
activity_service = ActivityService()
evidence_service = EvidenceService()
history_service = HistoryService()
dept_repo = DepartmentRepository()
domain_repo = DomainAreaRepository()
user_repo = UserRepository()

def can_user_view_activity(user_id: str, role: str, dept_id: str, activity) -> bool:
    """
    Object-level authorization policy for viewing activities and evidence (FR-005, FR-014, NFR-007).
    Limits visibility strictly according to institutional role and organizational scope.
    Students cannot view internal faculty activities or evidence documents.
    """
    if role in [Role.IQAC_COORDINATOR.value, Role.IQAC_MEMBER.value, Role.ADMINISTRATOR.value]:
        return True
    if role == Role.DEPARTMENT_COORDINATOR.value:
        return activity.departmentId == dept_id
    if role == Role.FACULTY_STAFF.value:
        return activity.assignedTo == user_id
    if role == Role.STUDENT.value:
        return False
    return False

@activity_bp.route("/activities")
@login_required
def list_activities():
    user_id = session.get("user_id")
    user_role = session.get("role")
    user_dept = session.get("department_id")

    # Students do not participate in faculty activities (SRS Section 11.1)
    if user_role == Role.STUDENT.value:
        flash("Students do not participate in internal faculty activities. Please submit feedback using the Feedback Forms portal.", "info")
        return redirect(url_for("feedback.list_feedback_forms"))

    status = request.args.get("status", "All")
    department_id = request.args.get("department_id")
    my_only = request.args.get("my_only", "false").lower() == "true"

    # Enforce role-based default scoping
    if department_id is None:
        if user_role == Role.DEPARTMENT_COORDINATOR.value:
            department_id = user_dept or "All"
        elif user_role == Role.FACULTY_STAFF.value:
            department_id = user_dept or "All"
        else:
            department_id = "All"

    assignee_id = user_id if (my_only or user_role == Role.STUDENT.value) else None

    # Coordinators cannot browse outside their department via query tampering
    if user_role == Role.DEPARTMENT_COORDINATOR.value and department_id != user_dept and department_id != "All":
        department_id = user_dept

    activities = activity_service.listActivities(status=status, departmentId=department_id, assigneeId=assignee_id)

    # Secondary filter to enforce object-level visibility
    activities = [a for a in activities if can_user_view_activity(user_id, user_role, user_dept, a)]

    departments = dept_repo.findAll()

    return render_template(
        "activities.html",
        activities=activities,
        departments=departments,
        current_status=status,
        current_dept=department_id,
        my_only=my_only
    )

@activity_bp.route("/activities/create", methods=["GET", "POST"])
@login_required
@roles_required(Role.DEPARTMENT_COORDINATOR, Role.IQAC_COORDINATOR, Role.ADMINISTRATOR)
def create_activity():
    user_role = session.get("role")
    user_dept = session.get("department_id")

    departments = dept_repo.findAll()
    domains = domain_repo.findAll()
    staff_users = user_repo.findAll()
    from models.enums import Role as _Role
    all_users = user_repo.findAll()
    staff_users = [u for u in all_users if u.role.value in [_Role.FACULTY_STAFF.value, _Role.DEPARTMENT_COORDINATOR.value]]

    if request.method == "POST":
        coordinator_id = session.get("user_id")

        # BR-001: Dept Coordinator can only create for their own department
        target_dept = request.form.get("department_id", "")
        if user_role == Role.DEPARTMENT_COORDINATOR.value:
            target_dept = user_dept

        details = {
            "title": request.form.get("title", ""),
            "description": request.form.get("description", ""),
            "departmentId": target_dept,
            "domainId": request.form.get("domain_id", ""),
            "plannedStart": request.form.get("planned_start", ""),
            "deadline": request.form.get("deadline", ""),
            "priority": request.form.get("priority", Priority.MEDIUM.value),
            "assignedTo": request.form.get("assigned_to", "") or None
        }

        success, message, act = activity_service.createActivity(coordinator_id, details)
        if success:
            flash(message, "success")
            return redirect(url_for("activity.activity_details", activity_id=act.activityId))
        else:
            flash(message, "danger")

    return render_template(
        "create_activity.html",
        departments=departments,
        domains=domains,
        staff_users=staff_users,
        user_dept=user_dept,
        user_role=user_role
    )

@activity_bp.route("/activities/<activity_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required(Role.DEPARTMENT_COORDINATOR, Role.IQAC_COORDINATOR, Role.ADMINISTRATOR)
def edit_activity(activity_id):
    """FR-009, FR-012: Edit activity title, description, deadline, priority."""
    user_id = session.get("user_id")
    user_role = session.get("role")
    user_dept = session.get("department_id")

    act = activity_service.getActivity(activity_id)
    if not act:
        flash("Activity not found.", "danger")
        return redirect(url_for("activity.list_activities"))

    # Authorization check
    if user_role == Role.DEPARTMENT_COORDINATOR.value and act.departmentId != user_dept:
        flash("Access Forbidden: You can only edit activities in your own department.", "danger")
        return redirect(url_for("activity.activity_details", activity_id=activity_id))

    if act.status.value in ["VERIFIED", "CANCELLED"]:
        flash(f"Cannot edit a {act.status.value} activity.", "danger")
        return redirect(url_for("activity.activity_details", activity_id=activity_id))

    if request.method == "POST":
        details = {
            "title": request.form.get("title", "").strip(),
            "description": request.form.get("description", "").strip(),
            "deadline": request.form.get("deadline", "").strip(),
            "planned_start": request.form.get("planned_start", "").strip(),
            "priority": request.form.get("priority", "").strip(),
            "domain_id": request.form.get("domain_id", "").strip(),
        }
        success, message = activity_service.editActivity(activity_id, user_id, user_role, user_dept, details)
        if success:
            flash(message, "success")
            return redirect(url_for("activity.activity_details", activity_id=activity_id))
        else:
            flash(message, "danger")

    domains = domain_repo.findAll()
    return render_template("edit_activity.html", activity=act, domains=domains)

@activity_bp.route("/activities/<activity_id>/reassign", methods=["POST"])
@login_required
@roles_required(Role.DEPARTMENT_COORDINATOR, Role.IQAC_COORDINATOR, Role.ADMINISTRATOR)
def reassign_activity(activity_id):
    """FR-011: Reassign activity to a new staff member."""
    user_id = session.get("user_id")
    user_role = session.get("role")
    user_dept = session.get("department_id")
    new_assignee_id = request.form.get("new_assignee_id", "").strip()

    if not new_assignee_id:
        flash("Please select a staff member to reassign to.", "danger")
        return redirect(url_for("activity.activity_details", activity_id=activity_id))

    success, message = activity_service.reassignActivity(activity_id, user_id, user_role, user_dept, new_assignee_id)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for("activity.activity_details", activity_id=activity_id))

@activity_bp.route("/activities/<activity_id>/update-status", methods=["POST"])
@login_required
def update_status(activity_id):
    """FR-020, FR-021: Update progress status and add remarks (faculty/staff + coordinators)."""
    user_id = session.get("user_id")
    user_role = session.get("role")
    user_dept = session.get("department_id")

    new_status = request.form.get("status", "").strip()
    remarks = request.form.get("remarks", "").strip()

    if not new_status:
        flash("Please select a status.", "danger")
        return redirect(url_for("activity.activity_details", activity_id=activity_id))

    success, message = activity_service.updateStatusByUser(activity_id, new_status, user_id, user_role, user_dept, remarks)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for("activity.activity_details", activity_id=activity_id))

@activity_bp.route("/activities/<activity_id>")
@login_required
def activity_details(activity_id):
    user_id = session.get("user_id")
    user_role = session.get("role")
    user_dept = session.get("department_id")

    activity = activity_service.getActivity(activity_id)
    if not activity:
        flash("Activity not found.", "danger")
        return redirect(url_for("activity.list_activities"))

    # Strict Object-Level Authorization Check (FR-005, NFR-008)
    if not can_user_view_activity(user_id, user_role, user_dept, activity):
        flash("Access Forbidden: You are not authorized to view activities outside your designated scope.", "danger")
        return redirect(url_for("activity.list_activities"))

    evidence_list = evidence_service.listEvidence(activity_id)
    history_logs = history_service.getActivityHistory(activity_id)
    assignee = user_repo.findById(activity.assignedTo) if activity.assignedTo else None

    # Build staff list for reassignment form (only FACULTY_STAFF + DEPT_COORDINATOR of same department)
    all_staff = user_repo.findAll(departmentId=activity.departmentId)
    staff_users = [u for u in all_staff if u.role.value in [Role.FACULTY_STAFF.value, Role.DEPARTMENT_COORDINATOR.value]]

    # Check edit permissions (BR-005)
    can_modify = (
        user_id == activity.assignedTo
        or (user_role == Role.DEPARTMENT_COORDINATOR.value and user_dept == activity.departmentId)
        or user_role in [Role.IQAC_COORDINATOR.value, Role.ADMINISTRATOR.value]
    )

    return render_template(
        "activity_details.html",
        activity=activity,
        evidence_list=evidence_list,
        history_logs=history_logs,
        assignee_name=assignee.name if assignee else "Unassigned",
        can_modify=can_modify,
        staff_users=staff_users
    )

@activity_bp.route("/activities/<activity_id>/upload-evidence", methods=["POST"])
@login_required
def upload_evidence(activity_id):
    user_id = session.get("user_id")
    role = session.get("role")
    dept = session.get("department_id")

    act = activity_service.getActivity(activity_id)
    if not act:
        flash("Activity not found.", "danger")
        return redirect(url_for("activity.list_activities"))

    # BR-005: Only assigned user or authorised coordinator/admin
    if act.assignedTo != user_id and not (role == Role.DEPARTMENT_COORDINATOR.value and dept == act.departmentId) and role not in [Role.IQAC_COORDINATOR.value, Role.ADMINISTRATOR.value]:
        flash("Forbidden: You are not authorized to upload evidence for this activity (BR-005).", "danger")
        return redirect(url_for("activity.activity_details", activity_id=activity_id))

    file = request.files.get("file")
    desc = request.form.get("description", "")

    success, message, ev = evidence_service.uploadEvidence(activity_id, user_id, file, desc)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for("activity.activity_details", activity_id=activity_id))

@activity_bp.route("/activities/<activity_id>/delete-evidence/<evidence_id>", methods=["POST"])
@login_required
def delete_evidence(activity_id, evidence_id):
    """FR-030 & BR-008: Remove wrongly uploaded evidence with ownership & role validation."""
    user_id = session.get("user_id")
    user_role = session.get("role")
    user_dept = session.get("department_id")

    success, message = evidence_service.deleteEvidence(
        evidenceId=evidence_id,
        userId=user_id,
        userRole=user_role,
        userDept=user_dept
    )
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for("activity.activity_details", activity_id=activity_id))

@activity_bp.route("/activities/<activity_id>/download-evidence/<evidence_id>")
@login_required
def download_evidence(activity_id, evidence_id):
    """Object-level authorization check on evidence file download (NFR-007, C-09)."""
    user_id = session.get("user_id")
    user_role = session.get("role")
    user_dept = session.get("department_id")

    act = activity_service.getActivity(activity_id)
    if not act:
        flash("Activity not found.", "danger")
        return redirect(url_for("activity.list_activities"))

    # Verify user has permission to view the activity this evidence belongs to
    if not can_user_view_activity(user_id, user_role, user_dept, act):
        flash("Access Forbidden: You are not authorized to download evidence from this activity.", "danger")
        return redirect(url_for("activity.list_activities"))

    ev = evidence_service.getEvidence(evidence_id)
    if not ev or ev.activityId != activity_id:
        flash("Evidence not found for this activity.", "danger")
        return redirect(url_for("activity.activity_details", activity_id=activity_id))

    try:
        path = evidence_service.file_store.open(ev.filePath)
        return send_file(path, as_attachment=False, download_name=ev.fileName)
    except FileNotFoundError:
        flash("File binary not found on disk.", "danger")
        return redirect(url_for("activity.activity_details", activity_id=activity_id))

@activity_bp.route("/activities/<activity_id>/outcome", methods=["POST"])
@login_required
def record_outcome(activity_id):
    user_id = session.get("user_id")
    role = session.get("role")
    dept = session.get("department_id")

    act = activity_service.getActivity(activity_id)
    if not act:
        flash("Activity not found.", "danger")
        return redirect(url_for("activity.list_activities"))

    # BR-005
    if act.assignedTo != user_id and not (role == Role.DEPARTMENT_COORDINATOR.value and dept == act.departmentId) and role not in [Role.IQAC_COORDINATOR.value, Role.ADMINISTRATOR.value]:
        flash("Forbidden: You are not authorized to update this activity (BR-005).", "danger")
        return redirect(url_for("activity.activity_details", activity_id=activity_id))

    outcome = request.form.get("outcome", "")
    success, message = activity_service.recordOutcome(activity_id, outcome, userId=user_id)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for("activity.activity_details", activity_id=activity_id))

@activity_bp.route("/activities/<activity_id>/submit", methods=["POST"])
@login_required
def submit_verification(activity_id):
    user_id = session.get("user_id")
    role = session.get("role")
    dept = session.get("department_id")

    act = activity_service.getActivity(activity_id)
    if not act:
        flash("Activity not found.", "danger")
        return redirect(url_for("activity.list_activities"))

    # SRS UC-010: Primarily the assigned Faculty/Staff submits; Dept Coordinator can submit for their dept
    is_assignee = act.assignedTo == user_id
    is_dept_coord_for_this_dept = (role == Role.DEPARTMENT_COORDINATOR.value and dept == act.departmentId)
    if not (is_assignee or is_dept_coord_for_this_dept):
        flash("Forbidden: Only the assigned Faculty/Staff member or the Department Coordinator may submit this activity for verification (UC-010, BR-005).", "danger")
        return redirect(url_for("activity.activity_details", activity_id=activity_id))

    # Must have at least 1 evidence file
    evidence_list = evidence_service.listEvidence(activity_id)
    if not evidence_list:
        flash("Cannot submit activity for verification without uploading evidence.", "danger")
        return redirect(url_for("activity.activity_details", activity_id=activity_id))

    success, message = activity_service.submitForVerification(activity_id, user_id)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for("activity.activity_details", activity_id=activity_id))

@activity_bp.route("/activities/<activity_id>/cancel", methods=["POST"])
@login_required
@roles_required(Role.DEPARTMENT_COORDINATOR, Role.IQAC_COORDINATOR, Role.ADMINISTRATOR)
def cancel_activity(activity_id):
    user_id = session.get("user_id")
    user_role = session.get("role")
    user_dept = session.get("department_id")

    act = activity_service.getActivity(activity_id)
    if not act:
        flash("Activity not found.", "danger")
        return redirect(url_for("activity.list_activities"))

    # Coordinator department match
    if user_role == Role.DEPARTMENT_COORDINATOR.value and act.departmentId != user_dept:
        flash("Access Forbidden: You can only cancel activities in your own department.", "danger")
        return redirect(url_for("activity.activity_details", activity_id=activity_id))

    reason = request.form.get("reason", "").strip()
    success, message = activity_service.cancelActivity(activity_id, user_id, reason)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for("activity.activity_details", activity_id=activity_id))

@activity_bp.route("/criteria", methods=["GET", "POST"])
@login_required
@roles_required(Role.IQAC_COORDINATOR)
def manage_criteria():
    """UC-003: Define Quality Domain Areas and Criteria (IQAC Coordinator only)."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Criterion name is required.", "danger")
            return redirect(url_for("activity.manage_criteria"))

        # Sequential, unique ID auto-generated by the system (e.g. CRITERION-1, CRITERION-2, ...)
        domain_id = domain_repo.getNextCriterionId()

        from models.domain_area import DomainArea
        area = DomainArea(domainId=domain_id, name=name, description=description)
        domain_repo.save(area)
        flash(f"Quality Criterion '{domain_id} - {name}' created successfully.", "success")
        return redirect(url_for("activity.manage_criteria"))

    criteria = domain_repo.findAll()
    criteria_with_counts = []
    for c in criteria:
        cnt = domain_repo.countLinkedActivities(c.domainId)
        criteria_with_counts.append({"criterion": c, "linked_count": cnt})

    next_id = domain_repo.getNextCriterionId()
    return render_template("criteria_list.html", criteria=criteria_with_counts, next_id=next_id)

@activity_bp.route("/criteria/<domain_id>/delete", methods=["POST"])
@login_required
@roles_required(Role.IQAC_COORDINATOR)
def delete_criterion(domain_id):
    """Delete an existing Quality Criterion (IQAC Coordinator only)."""
    criterion = domain_repo.findById(domain_id)
    if not criterion:
        flash("Criterion not found.", "danger")
        return redirect(url_for("activity.manage_criteria"))

    linked_count = domain_repo.countLinkedActivities(domain_id)
    if linked_count > 0:
        flash(f"Cannot delete '{domain_id}': {linked_count} {'activity is' if linked_count == 1 else 'activities are'} currently tagged to this criterion. Reassign those activities first.", "danger")
        return redirect(url_for("activity.manage_criteria"))

    domain_repo.delete(domain_id)
    flash(f"Quality Criterion '{domain_id}' ({criterion.name}) deleted successfully.", "success")
    return redirect(url_for("activity.manage_criteria"))
