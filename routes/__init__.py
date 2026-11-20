from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.profile_routes import profile_bp
from routes.activity_routes import activity_bp
from routes.verification_routes import verification_bp
from routes.report_routes import report_bp
from routes.feedback_routes import feedback_bp
from routes.admin_routes import admin_bp

__all__ = [
    "auth_bp",
    "dashboard_bp",
    "profile_bp",
    "activity_bp",
    "verification_bp",
    "report_bp",
    "feedback_bp",
    "admin_bp"
]
