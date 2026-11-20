import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from routes.auth_routes import login_required, roles_required
from models.enums import Role
from repositories.user_repository import UserRepository
from repositories.database import get_db_connection

admin_bp = Blueprint("admin", __name__)
user_repo = UserRepository()

@admin_bp.route("/admin/users")
@login_required
@roles_required(Role.ADMINISTRATOR)
def list_users():
    """FR-004, UC-002: View user accounts and their assigned roles."""
    users = user_repo.findAll()
    all_roles = [r.value for r in Role]
    return render_template("admin_users.html", users=users, roles=all_roles)

@admin_bp.route("/admin/users/<user_id>/role", methods=["POST"])
@login_required
@roles_required(Role.ADMINISTRATOR)
def assign_role(user_id):
    """FR-004 & Table 5: assignRoles(userId: String, role: Role) -> void, with audit trail (FR-053)."""
    admin_id = session.get("user_id")
    new_role = request.form.get("role")

    user = user_repo.findById(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin.list_users"))

    old_role = user.role.value if hasattr(user.role, "value") else str(user.role)
    if new_role == old_role:
        flash("User already holds this role.", "info")
        return redirect(url_for("admin.list_users"))

    success = user_repo.updateRole(user_id, new_role)
    if success:
        # Record significant administrative action in admin_audit_log (FR-053)
        conn = get_db_connection()
        cursor = conn.cursor()
        audit_id = f"AUDIT-{uuid.uuid4().hex[:6].upper()}"
        cursor.execute(
            """
            INSERT INTO admin_audit_log (audit_id, admin_id, target_user_id, action, details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                audit_id,
                admin_id,
                user_id,
                "ROLE_CHANGE",
                f"Changed role from {old_role} to {new_role}",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )
        conn.commit()
        conn.close()

        flash(f"Successfully updated role for {user.name} ({user_id}) to {new_role}.", "success")
    else:
        flash("Failed to update user role.", "danger")

    return redirect(url_for("admin.list_users"))
