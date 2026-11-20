import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    """Configuration for IQAC Activity Tracking System."""
    APP_NAME = os.getenv("APP_NAME", "IQAC Activity Tracking System")
    SECRET_KEY = os.getenv("SECRET_KEY", "iqac_cs311_auth_services_secret_key")
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # Persistent Database
    DATABASE_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "iqac_system.db")

    # File uploads & storage utility settings (Section 45.4.14, FR-026, FR-027)
    UPLOAD_FOLDER = BASE_DIR / "uploads" / "evidence"
    MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit as per SRS
    ALLOWED_FORMATS = ["pdf", "docx", "jpg", "jpeg", "png"]

    # Google SMTP Settings for OTP Authentication and Notifications (FR-001, FR-041)
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASS = os.getenv("SMTP_PASS", "")
    SMTP_FROM = os.getenv("SMTP_FROM", os.getenv("SMTP_USER", ""))
    SMTP_TLS = os.getenv("SMTP_TLS", "True").lower() in ("true", "1", "yes")

    # OTP expiration (10 minutes)
    OTP_EXPIRY_SECONDS = 600

    @classmethod
    def is_smtp_configured(cls) -> bool:
        """Check if active Google SMTP credentials are set in .env."""
        return bool(
            cls.SMTP_USER 
            and cls.SMTP_PASS 
            and "your_email" not in cls.SMTP_USER 
            and "xxxx" not in cls.SMTP_PASS
        )
