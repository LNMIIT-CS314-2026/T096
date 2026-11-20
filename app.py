import os
from flask import Flask, render_template, session
from config import Config
from repositories.database import init_db
from routes import (
    auth_bp,
    dashboard_bp,
    profile_bp,
    activity_bp,
    verification_bp,
    report_bp,
    feedback_bp,
    admin_bp
)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY

    # Ensure upload directory exists
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    # Initialize SQLite database
    init_db()

    # Start independent background deadline & overdue notification scheduler (FR-042, FR-043)
    from services.notification_service import start_background_notification_scheduler
    start_background_notification_scheduler()

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(activity_bp)
    app.register_blueprint(verification_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(admin_bp)

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("base.html", error_message="The requested resource could not be found (404)."), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("base.html", error_message="An internal server error occurred (500)."), 500

    @app.context_processor
    def inject_user_context():
        return {
            "current_user_id": session.get("user_id"),
            "current_user_name": session.get("name"),
            "current_user_role": session.get("role"),
            "current_user_dept": session.get("department_id"),
            "app_name": Config.APP_NAME
        }

    return app

if __name__ == "__main__":
    app = create_app()
    print(f"Starting {Config.APP_NAME} on http://localhost:{Config.PORT}")
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
