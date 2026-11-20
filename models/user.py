from abc import ABC
from typing import Optional, Any, List
from datetime import datetime
from models.enums import Role, AccountStatus, Priority, ActivityStatus

class User(ABC):
    """
    User entity holding profile information and authentication data
    as defined in Section 16 & Section 45.4.1.
    """
    def __init__(
        self,
        userId: str,
        name: str,
        email: str,
        passwordHash: str = "",
        role: Role | str = Role.FACULTY_STAFF,
        departmentId: Optional[str] = None,
        contactInfo: str = "",
        accountStatus: AccountStatus | str = AccountStatus.ACTIVE,
        createdAt: Optional[str] = None,
        updatedAt: Optional[str] = None
    ):
        self._userId = userId
        self._name = name
        self._email = email
        self._passwordHash = passwordHash
        self._role = role if isinstance(role, Role) else Role(role)
        self._departmentId = departmentId
        self._contactInfo = contactInfo
        self._accountStatus = (
            accountStatus if isinstance(accountStatus, AccountStatus) 
            else AccountStatus(accountStatus)
        )
        self._createdAt = createdAt or datetime.now().isoformat()
        self._updatedAt = updatedAt or datetime.now().isoformat()

    @property
    def userId(self) -> str:
        return self._userId

    @userId.setter
    def userId(self, value: str):
        self._userId = value

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str):
        self._email = value

    @property
    def passwordHash(self) -> str:
        return self._passwordHash

    @passwordHash.setter
    def passwordHash(self, value: str):
        self._passwordHash = value

    @property
    def role(self) -> Role:
        return self._role

    @role.setter
    def role(self, value: Role | str):
        self._role = value if isinstance(value, Role) else Role(value)

    @property
    def departmentId(self) -> Optional[str]:
        return self._departmentId

    @departmentId.setter
    def departmentId(self, value: Optional[str]):
        self._departmentId = value

    @property
    def contactInfo(self) -> str:
        return self._contactInfo

    @contactInfo.setter
    def contactInfo(self, value: str):
        self._contactInfo = value

    @property
    def accountStatus(self) -> AccountStatus:
        return self._accountStatus

    @accountStatus.setter
    def accountStatus(self, value: AccountStatus | str):
        self._accountStatus = (
            value if isinstance(value, AccountStatus) 
            else AccountStatus(value)
        )

    @property
    def createdAt(self) -> str:
        return self._createdAt

    @property
    def updatedAt(self) -> str:
        return self._updatedAt

    @updatedAt.setter
    def updatedAt(self, value: str):
        self._updatedAt = value

    def login(self, email: str, password: str) -> bool:
        """SRS Table 4: login(email: String, password: String) -> Boolean"""
        from services.auth_service import AuthService
        return self._email.lower() == email.strip().lower() and self._passwordHash == AuthService.hash_password(password)

    def logout(self) -> None:
        """SRS Table 4: logout() -> void"""
        pass

    def to_dict(self):
        return {
            "userId": self._userId,
            "name": self._name,
            "email": self._email,
            "role": self._role.value,
            "departmentId": self._departmentId,
            "contactInfo": self._contactInfo,
            "accountStatus": self._accountStatus.value,
            "createdAt": self._createdAt,
            "updatedAt": self._updatedAt
        }


class Administrator(User):
    def __init__(self, userId: str, name: str, email: str, passwordHash: str = "", departmentId: Optional[str] = None, contactInfo: str = "", accountStatus=AccountStatus.ACTIVE, createdAt=None, updatedAt=None):
        super().__init__(userId, name, email, passwordHash, Role.ADMINISTRATOR, departmentId, contactInfo, accountStatus, createdAt, updatedAt)

    def manageUsers(self, action: str, user: User) -> bool:
        """SRS Table 5: manageUsers(action: String, user: User) -> Boolean"""
        from repositories.user_repository import UserRepository
        repo = UserRepository()
        if action == "SAVE":
            repo.save(user)
            return True
        return False

    def assignRoles(self, userId: str, role: Role) -> None:
        """SRS Table 5: assignRoles(userId: String, role: Role) -> void"""
        from repositories.user_repository import UserRepository
        UserRepository().updateRole(userId, role)


class IQACMember(User):
    def __init__(self, userId: str, name: str, email: str, passwordHash: str = "", departmentId: Optional[str] = None, contactInfo: str = "", accountStatus=AccountStatus.ACTIVE, createdAt=None, updatedAt=None, role: Role = Role.IQAC_MEMBER):
        super().__init__(userId, name, email, passwordHash, role, departmentId, contactInfo, accountStatus, createdAt, updatedAt)

    def reviewSubmission(self, activityId: str):
        """SRS Table 6: reviewSubmission(activityId: String) -> List<Evidence>"""
        from repositories.evidence_repository import EvidenceRepository
        return EvidenceRepository().findByActivityId(activityId)

    def verifyActivity(self, activityId: str, comments: str = ""):
        """SRS Table 6: verifyActivity(activityId: String, comments: String) -> Verification"""
        from services.verification_service import VerificationService
        success, _, ver = VerificationService().verify(activityId, self._userId, comments)
        return ver

    def returnActivity(self, activityId: str, comments: str):
        """SRS Table 6: returnActivity(activityId: String, comments: String) -> Verification"""
        from services.verification_service import VerificationService
        success, _, ver = VerificationService().returnActivity(activityId, self._userId, comments)
        return ver


class IQACCoordinator(IQACMember):
    def __init__(self, userId: str, name: str, email: str, passwordHash: str = "", departmentId: Optional[str] = None, contactInfo: str = "", accountStatus=AccountStatus.ACTIVE, createdAt=None, updatedAt=None):
        super().__init__(userId, name, email, passwordHash, departmentId, contactInfo, accountStatus, createdAt, updatedAt, Role.IQAC_COORDINATOR)

    def defineDomainArea(self, name: str, description: str):
        """SRS Table 7: defineDomainArea(name: String, description: String) -> DomainArea"""
        from models.domain_area import DomainArea
        from repositories.department_repository import DomainAreaRepository
        repo = DomainAreaRepository()
        dom_id = repo.getNextCriterionId()
        area = DomainArea(domainId=dom_id, name=name, description=description)
        repo.save(area)
        return area

    def planActivities(self, domainId: str):
        """SRS Table 7: planActivities(domainId: String) -> List<Activity>"""
        from repositories.activity_repository import ActivityRepository
        all_acts = ActivityRepository().findAll()
        return [a for a in all_acts if a.domainId == domainId]


class DepartmentCoordinator(User):
    def __init__(self, userId: str, name: str, email: str, passwordHash: str = "", departmentId: Optional[str] = None, contactInfo: str = "", accountStatus=AccountStatus.ACTIVE, createdAt=None, updatedAt=None):
        super().__init__(userId, name, email, passwordHash, Role.DEPARTMENT_COORDINATOR, departmentId, contactInfo, accountStatus, createdAt, updatedAt)

    def createActivity(self, title: str, domainId: str, priority: Priority):
        """SRS Table 9: createActivity(title: String, domainId: String, priority: Priority) -> Activity"""
        from services.activity_service import ActivityService
        details = {
            "title": title,
            "domainId": domainId,
            "departmentId": self._departmentId or "CSE",
            "priority": priority.value if hasattr(priority, "value") else str(priority),
            "deadline": "2026-12-31"
        }
        success, _, act = ActivityService().createActivity(self._userId, details)
        return act

    def assignActivity(self, activityId: str, staffId: str) -> None:
        """SRS Table 9: assignActivity(activityId: String, staffId: String) -> void"""
        from repositories.activity_repository import ActivityRepository
        repo = ActivityRepository()
        act = repo.findById(activityId)
        if act:
            act.assign(staffId)
            repo.save(act)

    def setDeadline(self, activityId: str, deadline: str) -> None:
        """SRS Table 9: setDeadline(activityId: String, deadline: Date) -> void"""
        from repositories.activity_repository import ActivityRepository
        repo = ActivityRepository()
        act = repo.findById(activityId)
        if act:
            act.deadline = deadline
            repo.save(act)


class FacultyStaff(User):
    def __init__(self, userId: str, name: str, email: str, passwordHash: str = "", departmentId: Optional[str] = None, contactInfo: str = "", accountStatus=AccountStatus.ACTIVE, createdAt=None, updatedAt=None):
        super().__init__(userId, name, email, passwordHash, Role.FACULTY_STAFF, departmentId, contactInfo, accountStatus, createdAt, updatedAt)

    def updateStatus(self, activityId: str, status: ActivityStatus) -> None:
        """SRS Table 11: updateStatus(activityId: String, status: ActivityStatus) -> void"""
        from services.activity_service import ActivityService
        ActivityService().updateStatus(activityId, status, userId=self._userId)

    def uploadEvidence(self, activityId: str, file) -> Any:
        """SRS Table 11: uploadEvidence(activityId: String, file: File) -> Evidence"""
        from services.evidence_service import EvidenceService
        success, _, ev = EvidenceService().uploadEvidence(activityId, self._userId, file)
        return ev

    def recordOutcome(self, activityId: str, outcome: str) -> None:
        """SRS Table 11: recordOutcome(activityId: String, outcome: String) -> void"""
        from services.activity_service import ActivityService
        ActivityService().recordOutcome(activityId, outcome, userId=self._userId)


class Student(User):
    """
    SRS Section 11.1 & UC-019 Student Entity.
    Participates strictly in the feedback and quality survey response collection.
    """
    def __init__(self, userId: str, name: str, email: str, passwordHash: str = "", departmentId: Optional[str] = None, contactInfo: str = "", accountStatus=AccountStatus.ACTIVE, createdAt=None, updatedAt=None):
        super().__init__(userId, name, email, passwordHash, Role.STUDENT, departmentId, contactInfo, accountStatus, createdAt, updatedAt)

    def viewFeedbackForms(self, onlyOpen: bool = True):
        """SRS Section 11.1: view feedback forms."""
        from repositories.feedback_repository import FeedbackRepository
        return FeedbackRepository().findAllForms(onlyOpen=onlyOpen)

    def submitFeedback(self, formId: str, rating: int, comments: str = "") -> bool:
        """SRS Section 11.1 & UC-019: fill and submit feedback forms."""
        from repositories.feedback_repository import FeedbackRepository
        from models.feedback import FeedbackResponse
        import uuid
        repo = FeedbackRepository()
        if repo.hasUserSubmitted(formId, self._userId):
            return False
        resp = FeedbackResponse(
            responseId=f"RESP-{uuid.uuid4().hex[:6].upper()}",
            formId=formId,
            userId=self._userId,
            rating=rating,
            comments=comments
        )
        return repo.saveResponse(resp)

    def viewSubmissionHistory(self):
        """SRS Section 11.1: view their submission history."""
        from repositories.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM feedback_responses WHERE user_id = ? ORDER BY submitted_at DESC", (self._userId,))
        rows = cursor.fetchall()
        conn.close()
        return rows


def create_user_instance(
    userId: str,
    name: str,
    email: str,
    role: Role | str,
    passwordHash: str = "",
    departmentId: Optional[str] = None,
    contactInfo: str = "",
    accountStatus: AccountStatus | str = AccountStatus.ACTIVE,
    createdAt: Optional[str] = None,
    updatedAt: Optional[str] = None
) -> User:
    """Factory function creating the concrete subclass matching user role."""
    role_enum = Role(role) if isinstance(role, str) else role
    kwargs = {
        "userId": userId,
        "name": name,
        "email": email,
        "passwordHash": passwordHash,
        "departmentId": departmentId,
        "contactInfo": contactInfo,
        "accountStatus": accountStatus,
        "createdAt": createdAt,
        "updatedAt": updatedAt
    }
    if role_enum == Role.ADMINISTRATOR:
        return Administrator(**kwargs)
    elif role_enum == Role.IQAC_COORDINATOR:
        return IQACCoordinator(**kwargs)
    elif role_enum == Role.IQAC_MEMBER:
        return IQACMember(**kwargs)
    elif role_enum == Role.DEPARTMENT_COORDINATOR:
        return DepartmentCoordinator(**kwargs)
    elif role_enum == Role.STUDENT:
        return Student(**kwargs)
    else:
        return FacultyStaff(**kwargs)
