from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from services.auth_service import AuthService
from repositories.department_repository import DepartmentRepository
from models.enums import Role

auth_bp = Blueprint("auth", __name__)
auth_service = AuthService()
dept_repo = DepartmentRepository()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*allowed_roles):
    """Role-Based Access Control decorator (FR-005, BR-001, BR-010)."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("auth.login"))
            user_role = session.get("role")
            role_values = [r.value if hasattr(r, "value") else str(r) for r in allowed_roles]
            if user_role not in role_values:
                flash(f"Access Forbidden: You do not have permission for this operation (Role: {user_role}).", "danger")
                return redirect(url_for("dashboard.dashboard_view"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """FR-001: Authenticate using valid institutional credentials (Email & Password). No login via OTP."""
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard_view"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template("login.html", email=email)

        success, message, user = auth_service.authenticate(email, password)
        if success and user:
            session["user_id"] = user.userId
            session["name"] = user.name
            session["email"] = user.email
            session["role"] = user.role.value
            session["department_id"] = user.departmentId
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(url_for("dashboard.dashboard_view"))
        else:
            flash(message, "danger")
            return render_template("login.html", email=email)

    return render_template("login.html")

# --- Forgot Password Flow (OTP Protected) ---
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Step 1: Request password reset OTP to institutional email."""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if not email:
            flash("Please enter your institutional email.", "danger")
            return render_template("forgot_password.html")

        success, message, dev_otp = auth_service.requestPasswordResetOtp(email)
        if success:
            session["reset_email"] = email
            if dev_otp:
                flash(f"{message} [Test OTP: {dev_otp}]", "info")
            else:
                flash(message, "info")
            return redirect(url_for("auth.reset_password"))
        else:
            flash(message, "danger")
            return render_template("forgot_password.html", email=email)

    return render_template("forgot_password.html")

@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    """Step 2: Enter OTP and set new password."""
    email = session.get("reset_email") or request.args.get("email", "").strip() or request.form.get("email", "").strip()

    if request.method == "POST":
        otp_code = request.form.get("otp_code", "").strip()
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not email or not otp_code or not new_password:
            flash("All fields are required.", "danger")
            return render_template("reset_password.html", email=email)

        success, message = auth_service.resetPasswordWithOtp(
            email=email,
            otp_code=otp_code,
            new_password=new_password,
            confirm_password=confirm_password
        )
        if success:
            session.pop("reset_email", None)
            flash(message, "success")
            return redirect(url_for("auth.login"))
        else:
            flash(message, "danger")
            return render_template("reset_password.html", email=email)

    return render_template("reset_password.html", email=email)

@auth_bp.route("/resend-reset-otp", methods=["POST"])
def resend_reset_otp():
    email = request.form.get("email", "").strip()
    if email:
        success, message, dev_otp = auth_service.requestPasswordResetOtp(email)
        if success:
            if dev_otp:
                flash(f"New OTP sent. [Test OTP: {dev_otp}]", "info")
            else:
                flash("A new reset OTP has been sent to your email.", "info")
        else:
            flash(message, "danger")
    return redirect(url_for("auth.reset_password", email=email))

# --- New User Registration (OTP Protected) ---
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Step 1: Fill registration details and request verification OTP."""
    departments = dept_repo.findAll()
    # Security Rule: Only STUDENT role may be chosen during public registration; higher roles assigned by Admin
    public_roles = [Role.STUDENT.value]

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", Role.STUDENT.value)
        department_id = request.form.get("department_id")
        contact_info = request.form.get("contact_info", "").strip()

        # Reject any attempt to self-register into privileged roles
        if role != Role.STUDENT.value:
            flash(f"Privilege Escalation Blocked: Role '{role}' cannot be self-registered. Only Student registration is permitted; higher roles are provisioned by the Administrator.", "danger")
            return render_template(
                "register.html",
                departments=departments,
                roles=public_roles,
                form_data=request.form
            )

        # Validate inputs first
        valid, msg = auth_service.validateRegistrationInput(
            name=name,
            email=email,
            password=password,
            confirmPassword=confirm_password,
            role=role,
            departmentId=department_id,
            contactInfo=contact_info
        )
        if not valid:
            flash(msg, "danger")
            return render_template(
                "register.html",
                departments=departments,
                roles=public_roles,
                form_data=request.form
            )

        # Send verification OTP to new user's email
        success, otp_msg, dev_otp = auth_service.requestRegistrationOtp(email)
        if not success:
            flash(otp_msg, "danger")
            return render_template(
                "register.html",
                departments=departments,
                roles=public_roles,
                form_data=request.form
            )

        # Store pending registration temporarily in session
        session["pending_registration"] = {
            "name": name,
            "email": email,
            "password": password,
            "confirm_password": confirm_password,
            "role": role,
            "department_id": department_id,
            "contact_info": contact_info
        }

        if dev_otp:
            flash(f"Verification code sent! [Test OTP: {dev_otp}]", "info")
        else:
            flash("A 6-digit verification code has been dispatched to your email.", "info")

        return redirect(url_for("auth.verify_registration"))

    return render_template("register.html", departments=departments, roles=public_roles, form_data={})

@auth_bp.route("/register/verify", methods=["GET", "POST"])
def verify_registration():
    """Step 2: Enter 6-digit OTP to complete new user account creation."""
    pending = session.get("pending_registration")
    if not pending:
        flash("No registration in progress. Please fill the registration form.", "warning")
        return redirect(url_for("auth.register"))

    email = pending.get("email")

    if request.method == "POST":
        otp_code = request.form.get("otp_code", "").strip()
        if not otp_code:
            flash("Please enter the 6-digit OTP code.", "danger")
            return render_template("verify_registration_otp.html", email=email)

        success, message, user = auth_service.completeRegistration(
            name=pending["name"],
            email=pending["email"],
            password=pending["password"],
            confirmPassword=pending["confirm_password"],
            otp_code=otp_code,
            role=pending["role"],
            departmentId=pending["department_id"],
            contactInfo=pending["contact_info"]
        )

        if success and user:
            session.pop("pending_registration", None)
            flash(message, "success")
            return redirect(url_for("auth.login"))
        else:
            flash(message, "danger")
            return render_template("verify_registration_otp.html", email=email)

    return render_template("verify_registration_otp.html", email=email)

@auth_bp.route("/register/resend-otp", methods=["POST"])
def resend_registration_otp():
    pending = session.get("pending_registration")
    if not pending:
        flash("No pending registration session found.", "warning")
        return redirect(url_for("auth.register"))

    email = pending.get("email")
    success, msg, dev_otp = auth_service.requestRegistrationOtp(email)
    if success:
        if dev_otp:
            flash(f"New OTP code sent! [Test OTP: {dev_otp}]", "info")
        else:
            flash("A fresh verification code was sent to your email.", "info")
    else:
        flash(msg, "danger")
    return redirect(url_for("auth.verify_registration"))

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("auth.login"))
