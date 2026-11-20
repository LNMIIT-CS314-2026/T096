import uuid
from typing import Optional, List, Dict, Any, Tuple
from models.feedback import FeedbackForm, FeedbackResponse
from models.enums import Role
from repositories.feedback_repository import FeedbackRepository
from repositories.activity_repository import ActivityRepository

class FeedbackService:
    """
    SRS FR-036 - FR-040, BR-011, UC-018, UC-019:
    Unified Feedback Service.
    Enforces that:
    1. Only students can submit feedback responses (SRS Section 11.1, UC-019).
    2. Feedback forms can only be created by authorized coordinators/admins (FR-036).
    3. Forms enforce opens_at / closes_at date windows and isOpen flag (FR-037, BR-011).
    4. One response per student per form (FR-039 duplicate prevention).
    5. Feedback summaries are inspected by faculty/coordinators for quality assessment (FR-040).
    """
    def __init__(
        self,
        feedback_repo: Optional[FeedbackRepository] = None,
        activity_repo: Optional[ActivityRepository] = None
    ):
        self.feedback_repo = feedback_repo or FeedbackRepository()
        self.activity_repo = activity_repo or ActivityRepository()

    def listFormsForUser(self, userId: str) -> List[Dict[str, Any]]:
        all_forms = self.feedback_repo.findAllForms()
        result = []
        for f in all_forms:
            has_submitted = self.feedback_repo.hasUserSubmitted(f.formId, userId)
            result.append({
                "form": f,
                "has_submitted": has_submitted,
                "accepting": f.isAcceptingSubmissions()
            })
        return result

    def getForm(self, formId: str) -> Optional[FeedbackForm]:
        return self.feedback_repo.findFormById(formId)

    def submitResponse(
        self,
        formId: str,
        userId: str,
        userRole: str,
        rating: int,
        comments: str
    ) -> Tuple[bool, str]:
        # Enforce Student-only submission constraint (SRS Section 11.1 & UC-019)
        if userRole != Role.STUDENT.value:
            return False, "Access Restricted: Only students are eligible to submit feedback forms (SRS Section 11.1 & UC-019)."

        # Verify against user repository to guarantee only enrolled students can submit
        from repositories.user_repository import UserRepository
        user = UserRepository().findById(userId)
        if user:
            role_val = user.role.value if hasattr(user.role, 'value') else str(user.role)
            if role_val != Role.STUDENT.value:
                return False, "Access Restricted: Only students are eligible to submit feedback forms (SRS Section 11.1 & UC-019)."

        form = self.feedback_repo.findFormById(formId)
        if not form:
            return False, "Feedback form not found."

        # FR-037, BR-011: Check both isOpen AND date window via isAcceptingSubmissions()
        if not form.isAcceptingSubmissions():
            if not form.isOpen:
                return False, "Feedback submission closed: This form has been closed by the coordinator (BR-011)."
            return False, "Feedback submission outside window: This form is not yet open or has already closed (FR-037)."

        # FR-039: Duplicate prevention per user per form
        if self.feedback_repo.hasUserSubmitted(formId, userId):
            return False, "Duplicate submission rejected: You have already submitted feedback for this form (FR-039)."

        if not (1 <= rating <= 5):
            return False, "Rating must be an integer between 1 and 5."

        if len(comments) > 500:
            return False, "Feedback comments cannot exceed 500 characters."

        resp_id = f"RESP-{uuid.uuid4().hex[:6].upper()}"
        response = FeedbackResponse(
            responseId=resp_id,
            formId=formId,
            userId=userId,
            rating=rating,
            comments=comments
        )

        saved = self.feedback_repo.saveResponse(response)
        if not saved:
            return False, "Duplicate submission prevented. Response was already logged."

        return True, "Thank you! Your feedback has been recorded successfully."

    def createForm(
        self,
        title: str,
        activityId: str,
        createdBy: str,
        creatorRole: str,
        opensAt: Optional[str] = None,
        closesAt: Optional[str] = None
    ) -> Tuple[bool, str, Optional[FeedbackForm]]:
        if creatorRole not in [Role.IQAC_COORDINATOR.value, Role.ADMINISTRATOR.value]:
            return False, "Unauthorized: Only IQAC Coordinator or Administrator may create feedback forms.", None

        title = title.strip()
        if not title:
            return False, "Form title is required.", None
        if len(title) > 150:
            return False, "Form title cannot exceed 150 characters.", None

        if not activityId:
            return False, "Linked activity is required.", None

        activity = self.activity_repo.findById(activityId)
        if not activity:
            return False, "Linked activity not found.", None

        # Ensure defined opening and closing date window (FR-037, BR-011)
        from datetime import date as _d, timedelta as _td, datetime as _dt
        if not opensAt:
            opensAt = _d.today().isoformat()
        if not closesAt:
            if activity.deadline:
                closesAt = activity.deadline[:10]
            else:
                closesAt = (_d.today() + _td(days=30)).isoformat()

        # Validate date window
        try:
            o = _dt.strptime(opensAt[:10], "%Y-%m-%d").date()
            c = _dt.strptime(closesAt[:10], "%Y-%m-%d").date()
            if c < o:
                return False, "Closing date cannot be before opening date.", None
        except ValueError:
            return False, "Invalid date format for opens/closes window.", None

        form_id = f"FB-{uuid.uuid4().hex[:6].upper()}"
        new_form = FeedbackForm(
            formId=form_id,
            title=title,
            activityId=activityId,
            targetRole="STUDENT",
            isOpen=True,
            createdBy=createdBy,
            opensAt=opensAt,
            closesAt=closesAt
        )
        self.feedback_repo.saveForm(new_form)
        return True, f"Feedback Form '{title}' published successfully for students!", new_form

    def getSummary(self, formId: str, userRole: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        role_val = userRole.value if hasattr(userRole, "value") else str(userRole or "")
        if role_val == Role.STUDENT.value:
            return False, "Unauthorized: Student role cannot inspect aggregated feedback data.", None

        form = self.feedback_repo.findFormById(formId)
        if not form:
            return False, "Feedback form not found.", None

        responses = self.feedback_repo.getResponsesByFormId(formId)
        avg_rating = round(sum(r.rating for r in responses) / len(responses), 2) if responses else 0.0

        return True, "Summary retrieved.", {
            "form": form,
            "responses": responses,
            "avg_rating": avg_rating,
            "total_responses": len(responses)
        }
