from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from routes.auth_routes import login_required
from services.profile_service import ProfileService
from repositories.department_repository import DepartmentRepository

profile_bp = Blueprint("profile", __name__)
profile_service = ProfileService()
dept_repo = DepartmentRepository()

@profile_bp.route("/profile")
@login_required
def view_profile():
    """Displays comprehensive profile information for the authenticated user."""
    user_id = session.get("user_id")
    success, message, data = profile_service.getProfile(user_id)
    if not success or not data:
        flash("Could not load user profile.", "danger")
        return redirect(url_for("auth.logout"))

    return render_template(
        "profile.html",
        user=data["user"],
        department=data["department"]
    )

@profile_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    """Edit user profile details (Name, Contact info, Department)."""
    user_id = session.get("user_id")
    departments = dept_repo.findAll()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        contact_info = request.form.get("contact_info", "").strip()
        department_id = request.form.get("department_id")

        success, message = profile_service.updateProfile(
            userId=user_id,
            name=name,
            contactInfo=contact_info,
            departmentId=department_id
        )

        if success:
            session["name"] = name
            session["department_id"] = department_id
            flash(message, "success")
            return redirect(url_for("profile.view_profile"))
        else:
            flash(message, "danger")

    success, message, data = profile_service.getProfile(user_id)
    return render_template(
        "edit_profile.html",
        user=data["user"] if data else None,
        departments=departments
    )

@profile_bp.route("/profile/request-password-otp", methods=["POST"])
@login_required
def request_password_otp():
    """Dispatches security OTP to the logged in user's institutional email."""
    user_id = session.get("user_id")
    success, message, dev_otp = profile_service.requestPasswordChangeOtp(user_id)
    if success:
        if dev_otp:
            flash(f"{message} [Test OTP: {dev_otp}]", "info")
        else:
            flash(message, "info")
    else:
        flash(message, "danger")
    return redirect(url_for("profile.edit_profile") + "#password-section")

@profile_bp.route("/profile/change-password", methods=["POST"])
@login_required
def change_password():
    """Change account password with strict constraints and mandatory OTP."""
    user_id = session.get("user_id")
    current_password = request.form.get("current_password", "")
    otp_code = request.form.get("otp_code", "").strip()
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    success, message = profile_service.changePasswordWithOtp(
        userId=user_id,
        currentPassword=current_password,
        otpCode=otp_code,
        newPassword=new_password,
        confirmPassword=confirm_password
    )

    if success:
        flash(message, "success")
        return redirect(url_for("profile.view_profile"))
    else:
        flash(message, "danger")
        return redirect(url_for("profile.edit_profile") + "#password-section")
