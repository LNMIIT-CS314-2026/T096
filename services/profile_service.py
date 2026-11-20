import re
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from config import Config
from models.user import User
from models.enums import Role, AccountStatus
from repositories.user_repository import UserRepository
from repositories.department_repository import DepartmentRepository
from services.auth_service import AuthService
from utils.email_sender import EmailSender

class ProfileService:
    """
    Manages User Profiling, profile updates, and OTP-secured password updates
    while enforcing all institutional data constraints and character limits.
    """
    def __init__(
        self,
        user_repo: Optional[UserRepository] = None,
        dept_repo: Optional[DepartmentRepository] = None
    ):
        self.user_repo = user_repo or UserRepository()
        self.dept_repo = dept_repo or DepartmentRepository()

    def getProfile(self, userId: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Loads complete user profile along with affiliated department information."""
        user = self.user_repo.findById(userId)
        if not user:
            return False, "User not found.", None

        department = None
        if user.departmentId:
            department = self.dept_repo.findById(user.departmentId)

        data = {
            "user": user,
            "department": department
        }
        return True, "Profile retrieved successfully.", data

    def updateProfile(
        self,
        userId: str,
        name: str,
        contactInfo: str = "",
        departmentId: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Updates profile details while validating constraints and character limits.
        - Name: 2 - 70 chars
        - Contact info: 7 - 20 chars
        - Department: valid department
        """
        user = self.user_repo.findById(userId)
        if not user:
            return False, "User account not found."

        clean_name = name.strip()
        if not clean_name or len(clean_name) < 2:
            return False, "Full name must be at least 2 characters."
        if len(clean_name) > 70:
            return False, "Full name cannot exceed 70 characters."

        clean_contact = contactInfo.strip()
        if clean_contact:
            if len(clean_contact) > 20:
                return False, "Contact information cannot exceed 20 characters."
            if not re.match(r"^[\d\+\-\s\(\)]{7,20}$", clean_contact):
                return False, "Contact information must be a valid phone number (7-20 digits)."

        clean_dept = departmentId.strip() if departmentId else None
        if clean_dept:
            dept = self.dept_repo.findById(clean_dept)
            if not dept:
                return False, f"Invalid department ID: {clean_dept}"

        success = self.user_repo.updateProfile(userId, clean_name, clean_contact, clean_dept)
        if success:
            return True, "Profile details updated successfully."
        return False, "Failed to update profile."

    def requestPasswordChangeOtp(self, userId: str) -> Tuple[bool, str, Optional[str]]:
        """Dispatches OTP to the user's institutional email before allowing password change."""
        user = self.user_repo.findById(userId)
        if not user:
            return False, "User account not found.", None

        otp_code = f"{secrets.randbelow(900000) + 100000}"
        expires_at = datetime.now() + timedelta(seconds=Config.OTP_EXPIRY_SECONDS)
        self.user_repo.saveOtp(user.email, otp_code, expires_at)

        sent = EmailSender.send_otp_email(user.email, otp_code)
        if sent:
            return True, f"Security OTP sent to {user.email}.", None
        else:
            return (
                True,
                f"Security OTP generated. (Development OTP: {otp_code})",
                otp_code if Config.DEBUG else None
            )

    def changePasswordWithOtp(
        self,
        userId: str,
        currentPassword: str,
        otpCode: str,
        newPassword: str,
        confirmPassword: str
    ) -> Tuple[bool, str]:
        """
        Enforces password update constraints with mandatory OTP:
        - Current password must be valid
        - OTP code must be valid and verified
        - New password length (6 - 64 characters)
        - New password cannot match current password
        - New password and confirmation must match
        """
        user = self.user_repo.findById(userId)
        if not user:
            return False, "User not found."

        # Verify current password
        curr_hash = AuthService.hash_password(currentPassword)
        if user.passwordHash and user.passwordHash != curr_hash:
            return False, "Current password is incorrect."

        # Verify OTP code
        clean_otp = otpCode.strip()
        if not re.match(r"^\d{6}$", clean_otp):
            return False, "Security OTP must be a 6-digit number."

        if not self.user_repo.verifyOtp(user.email, clean_otp):
            return False, "Invalid or expired OTP code. Please request a new code."

        if len(newPassword) < 6:
            return False, "New password must be at least 6 characters in length."
        if len(newPassword) > 64:
            return False, "New password cannot exceed 64 characters."

        if newPassword != confirmPassword:
            return False, "New password and confirmation do not match."

        if currentPassword == newPassword:
            return False, "New password cannot be the same as current password."

        new_hash = AuthService.hash_password(newPassword)
        success = self.user_repo.updatePassword(userId, new_hash)
        if success:
            return True, "Password changed successfully!"
        return False, "Could not update password."
