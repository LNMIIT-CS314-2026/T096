import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

logger = logging.getLogger(__name__)

class EmailSender:
    """
    Handles Google SMTP email transmission for OTP authentication and notifications.
    Supports secure STARTTLS over port 587 or SSL over 465.
    """
    @staticmethod
    def send_email(to_email: str, subject: str, html_body: str, text_body: str = "") -> bool:
        if not Config.is_smtp_configured():
            logger.warning(
                f"[DEV MODE - SMTP Not Configured] To: {to_email} | Subject: {subject}\n"
                f"Body Preview: {text_body or html_body[:120]}"
            )
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{Config.APP_NAME} <{Config.SMTP_FROM}>"
            msg["To"] = to_email

            if text_body:
                msg.attach(MIMEText(text_body, "plain"))
            if html_body:
                msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=10) as server:
                if Config.SMTP_TLS:
                    server.starttls()
                server.login(Config.SMTP_USER, Config.SMTP_PASS)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email} via Google SMTP: {e}")
            return False

    @classmethod
    def send_otp_email(cls, to_email: str, otp_code: str) -> bool:
        """Sends OTP verification email to the user."""
        subject = f"Your Login OTP for {Config.APP_NAME}"
        text_body = (
            f"Hello,\n\n"
            f"Your one-time authentication code for the IQAC Activity Tracking System is:\n\n"
            f"{otp_code}\n\n"
            f"This code will expire in {Config.OTP_EXPIRY_SECONDS // 60} minutes.\n"
            f"If you did not request this login, please ignore this email.\n\n"
            f"Regards,\nIQAC Team"
        )
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 520px; margin: auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px; background-color: #ffffff;">
            <h2 style="color: #1e3a8a; margin-top: 0;">IQAC Activity Tracking System</h2>
            <p style="color: #4b5563; font-size: 15px;">Your One-Time Password (OTP) for authentication is:</p>
            <div style="margin: 20px 0; padding: 14px 24px; background-color: #f1f5f9; border-radius: 6px; font-size: 32px; font-weight: bold; letter-spacing: 6px; color: #1e40af; text-align: center;">
                {otp_code}
            </div>
            <p style="color: #64748b; font-size: 13px;">This code is valid for <strong>{Config.OTP_EXPIRY_SECONDS // 60} minutes</strong>. Please do not share it with anyone.</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
            <p style="color: #94a3b8; font-size: 12px; margin-bottom: 0;">Internal Quality Assurance Cell (IQAC)</p>
        </div>
        """
        return cls.send_email(to_email, subject, html_body, text_body)

    @classmethod
    def send_notification_email(cls, to_email: str, notification_type: str, message: str) -> bool:
        """Sends an activity notification email."""
        subject = f"[{Config.APP_NAME}] {notification_type.replace('_', ' ').title()}"
        text_body = f"Notification: {message}\n\nPlease log in to view details."
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 520px; margin: auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;">
            <h3 style="color: #1e3a8a;">IQAC System Notification</h3>
            <p style="color: #334155; font-size: 15px;">{message}</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
            <p style="color: #94a3b8; font-size: 12px;">Type: {notification_type}</p>
        </div>
        """
        return cls.send_email(to_email, subject, html_body, text_body)
