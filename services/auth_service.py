import re
import secrets
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple
from config import Config
from models.user import User, create_user_instance
from models.enums import Role, AccountStatus
from repositories.user_repository import UserRepository
from repositories.department_repository import DepartmentRepository
from utils.email_sender import EmailSender

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@lnmiit\.ac\.in$"

class AuthService:
    """
    Handles Institutional Credential Authentication (FR-001, FR-002),
    OTP-verified User Registration, and OTP-verified Password Reset.
    Strictly enforces:
    - NO login via OTP (login is strictly institutional email + password).
    - User registration requires 6-digit OTP verification.
    - Forgot password & password reset requires 6-digit OTP verification.
    - All fields strictly bounded by character limits.
    """
    def __init__(
        self,
        user_repo: Optional[UserRepository] = None,
        dept_repo: Optional[DepartmentRepository] = None
    ):
        self.user_repo = user_repo or UserRepository()
        self.dept_repo = dept_repo or DepartmentRepository()

    @staticmethod
    def hash_password(password: str) -> str:
        """Secure SHA-256 password hashing."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def authenticate(self, email: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """
        Validates email and password credentials (FR-001, FR-002, Table 4).
        Notifies user of failure without revealing whether email or password was wrong.
        """
        clean_email = email.strip().lower()
        if not clean_email or not password:
            return False, "Email and password are required.", None

        if len(clean_email) > 100:
            return False, "Email address exceeds maximum length of 100 characters.", None

        if len(password) > 64:
            return False, "Password exceeds maximum length of 64 characters.", None

        user = self.user_repo.findByEmail(clean_email)
        if not user:
            # FR-002: Do not leak whether email exists
            return False, "Authentication failed. Invalid email or password.", None

        if user.accountStatus != AccountStatus.ACTIVE:
            return False, f"Account is {user.accountStatus.value}. Please contact administrator.", None

        if not user.passwordHash or user.passwordHash != self.hash_password(password):
            return False, "Authentication failed. Invalid email or password.", None

        return True, "Authentication successful.", user

    # --- Registration Flow with OTP Verification ---
    def validateRegistrationInput(
        self,
        name: str,
        email: str,
        password: str,
        confirmPassword: str,
        role: Role | str,
        departmentId: Optional[str] = None,
        contactInfo: str = ""
    ) -> Tuple[bool, str]:
        """Validates all registration fields and character limits."""
        clean_name = name.strip()
        clean_email = email.strip().lower()
        clean_contact = contactInfo.strip()

        if len(clean_name) < 2:
            return False, "Full name must be at least 2 characters."
        if len(clean_name) > 70:
            return False, "Full name cannot exceed 70 characters."

        if not clean_email or not re.match(EMAIL_REGEX, clean_email):
            return False, "Please provide a valid institutional @lnmiit.ac.in email address."
        if len(clean_email) > 100:
            return False, "Email cannot exceed 100 characters."

        # Unique email constraint
        if self.user_repo.findByEmail(clean_email):
            return False, "An account with this email already exists."

        if clean_contact:
            # Mobile number must be exactly 10 digits (FR-001 registration constraint)
            digits = re.sub(r"[^\d]", "", clean_contact)
            if clean_contact.startswith("+91") or (len(digits) == 12 and digits.startswith("91")):
                digits = digits[-10:]
            if len(digits) != 10:
                return False, "Mobile number must be exactly 10 digits."

        if len(password) < 6:
            return False, "Password must be at least 6 characters in length."
        if len(password) > 64:
            return False, "Password cannot exceed 64 characters."

        if password != confirmPassword:
            return False, "Password and confirmation do not match."

        # Security Constraint: Only Student self-registration is allowed; higher roles provisioned by admin
        role_str = role.value if hasattr(role, "value") else str(role)
        if role_str != Role.STUDENT.value:
            return False, f"Privilege Escalation Rejected: Only the STUDENT role can be chosen during registration. Higher roles must be assigned by the Administrator."

        if departmentId:
            dept = self.dept_repo.findById(departmentId.strip())
            if not dept:
                return False, f"Invalid department ID: {departmentId}"

        return True, "Valid"

    def requestRegistrationOtp(self, email: str) -> Tuple[bool, str, Optional[str]]:
        """Generates and dispatches OTP for registering a new user."""
        clean_email = email.strip().lower()
        if not clean_email or not re.match(EMAIL_REGEX, clean_email):
            return False, "Please provide a valid institutional @lnmiit.ac.in email address.", None

        if self.user_repo.findByEmail(clean_email):
            return False, "An account with this email is already registered.", None

        otp_code = f"{secrets.randbelow(900000) + 100000}"
        expires_at = datetime.now() + timedelta(seconds=Config.OTP_EXPIRY_SECONDS)
        self.user_repo.saveOtp(clean_email, otp_code, expires_at)

        sent = EmailSender.send_otp_email(clean_email, otp_code)
        if sent:
            return True, f"Verification OTP sent to {clean_email}.", None
        else:
            return (
                True,
                f"OTP generated. (Development OTP: {otp_code})",
                otp_code if Config.DEBUG else None
            )

    def completeRegistration(
        self,
        name: str,
        email: str,
        password: str,
        confirmPassword: str,
        otp_code: str,
        role: Role | str = Role.FACULTY_STAFF,
        departmentId: Optional[str] = None,
        contactInfo: str = ""
    ) -> Tuple[bool, str, Optional[User]]:
        """Verifies OTP and creates the new user account."""
        clean_email = email.strip().lower()
        clean_otp = otp_code.strip()

        # Validate fields
        valid, msg = self.validateRegistrationInput(
            name=name,
            email=clean_email,
            password=password,
            confirmPassword=confirmPassword,
            role=role,
            departmentId=departmentId,
            contactInfo=contactInfo
        )
        if not valid:
            return False, msg, None

        if not re.match(r"^\d{6}$", clean_otp):
            return False, "OTP code must be a 6-digit number.", None

        if not self.user_repo.verifyOtp(clean_email, clean_otp):
            return False, "Invalid or expired OTP code. Please request a new code.", None

        # Double check role constraint before account creation
        role_str = role.value if hasattr(role, "value") else str(role)
        if role_str != Role.STUDENT.value:
            return False, "Privilege Escalation Rejected: Unapproved role for self-registration. Only STUDENT role is permitted.", None

        user_id = f"USR-{uuid.uuid4().hex[:6].upper()}"
        pwd_hash = self.hash_password(password)

        clean_contact = contactInfo.strip()
        if clean_contact:
            digits = re.sub(r"[^\d]", "", clean_contact)
            if clean_contact.startswith("+91") or (len(digits) == 12 and digits.startswith("91")):
                digits = digits[-10:]
            clean_contact = digits

        new_user = create_user_instance(
            userId=user_id,
            name=name.strip(),
            email=clean_email,
            passwordHash=pwd_hash,
            role=role,
            departmentId=departmentId.strip() if departmentId else None,
            contactInfo=clean_contact,
            accountStatus=AccountStatus.ACTIVE
        )
        self.user_repo.save(new_user)
        return True, "Account registered successfully with email verification! You can now log in.", new_user

    # --- Forgot Password & Reset Flow with OTP ---
    def requestPasswordResetOtp(self, email: str) -> Tuple[bool, str, Optional[str]]:
        """Sends OTP to user's registered institutional email for resetting password."""
        clean_email = email.strip().lower()
        if not clean_email or not re.match(EMAIL_REGEX, clean_email):
            return False, "Please enter a valid institutional email address.", None

        user = self.user_repo.findByEmail(clean_email)
        if not user:
            # For security, state OTP sent or return generic response
            return False, "No active user account found with this institutional email.", None

        if user.accountStatus != AccountStatus.ACTIVE:
            return False, f"Account is {user.accountStatus.value}. Please contact administrator.", None

        otp_code = f"{secrets.randbelow(900000) + 100000}"
        expires_at = datetime.now() + timedelta(seconds=Config.OTP_EXPIRY_SECONDS)
        self.user_repo.saveOtp(clean_email, otp_code, expires_at)

        sent = EmailSender.send_otp_email(clean_email, otp_code)
        if sent:
            return True, f"Password reset OTP sent to {clean_email}.", None
        else:
            return (
                True,
                f"Reset OTP generated. (Development OTP: {otp_code})",
                otp_code if Config.DEBUG else None
            )

    def resetPasswordWithOtp(
        self,
        email: str,
        otp_code: str,
        new_password: str,
        confirm_password: str
    ) -> Tuple[bool, str]:
        """Validates OTP and sets new password."""
        clean_email = email.strip().lower()
        clean_otp = otp_code.strip()

        if not re.match(r"^\d{6}$", clean_otp):
            return False, "OTP code must be a 6-digit number."

        if len(new_password) < 6:
            return False, "Password must be at least 6 characters in length."
        if len(new_password) > 64:
            return False, "Password cannot exceed 64 characters."

        if new_password != confirm_password:
            return False, "Password and confirmation do not match."

        if not self.user_repo.verifyOtp(clean_email, clean_otp):
            return False, "Invalid or expired OTP code. Please request a new code."

        user = self.user_repo.findByEmail(clean_email)
        if not user:
            return False, "User account not found."

        new_hash = self.hash_password(new_password)
        success = self.user_repo.updatePassword(user.userId, new_hash)
        if success:
            return True, "Password has been reset successfully! You can now log in."
        return False, "Failed to update password."
