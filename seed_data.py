import os
from pathlib import Path
from config import Config
from repositories.database import init_db
from repositories.department_repository import DepartmentRepository, DomainAreaRepository
from repositories.user_repository import UserRepository
from repositories.activity_repository import ActivityRepository
from repositories.evidence_repository import EvidenceRepository
from repositories.notification_repository import NotificationRepository
from repositories.history_repository import HistoryRepository
from repositories.feedback_repository import FeedbackRepository
from models.department import Department
from models.domain_area import DomainArea
from models.user import create_user_instance
from models.activity import Activity
from models.history_log import ActivityHistoryLog
from models.evidence import Evidence
from models.notification import Notification
from models.feedback import FeedbackForm, FeedbackResponse
from models.enums import Role, AccountStatus, Priority, ActivityStatus, VerificationStatus
from services.auth_service import AuthService

def seed_database():
    """Seeds the database with departments, criteria, users, activities, and evidence."""
    init_db()

    dept_repo = DepartmentRepository()
    domain_repo = DomainAreaRepository()
    user_repo = UserRepository()
    activity_repo = ActivityRepository()
    evidence_repo = EvidenceRepository()
    notif_repo = NotificationRepository()
    history_repo = HistoryRepository()

    # 1. Departments
    departments = [
        Department("CSE", "Computer Science & Engineering", "Dr. Rajesh Sharma", "cse.office@institution.edu"),
        Department("ECE", "Electronics & Communication Engineering", "Dr. Soumitra Debnath", "ece.office@institution.edu"),
        Department("ME", "Mechanical & Mechatronics Engineering", "Dr. Pravin Kumar", "me.office@institution.edu"),
        Department("HSS", "Humanities & Social Sciences", "Dr. Usha Kanoongo", "hss.office@institution.edu"),
    ]
    for d in departments:
        dept_repo.save(d)

    # 2. Quality Domain Areas (NAAC Criteria)
    domains = [
        DomainArea("CRITERION-1", "Curricular Aspects", "Curriculum enrichment, flexibility, and feedback systems"),
        DomainArea("CRITERION-2", "Teaching-Learning and Evaluation", "Student engagement, evaluation process, and attainment"),
        DomainArea("CRITERION-3", "Research, Innovations and Extension", "Publications, resource mobilization, and collaborations"),
        DomainArea("CRITERION-4", "Infrastructure & Learning Resources", "Campus IT, laboratory maintenance, and library systems"),
        DomainArea("CRITERION-5", "Student Support & Progression", "Mentoring, capacity development, and student welfare"),
        DomainArea("CRITERION-6", "Governance, Leadership & Management", "Institutional vision, strategic plans, and audits"),
        DomainArea("CRITERION-7", "Institutional Values & Best Practices", "Sustainability, green audits, and distinctive practices"),
    ]
    for dm in domains:
        domain_repo.save(dm)

    # 3. Institutional Users & Profiles
    default_pwd_hash = AuthService.hash_password("password123")
    users = [
        create_user_instance("staff01", "Ananya Rathore", "ananya.rathore@lnmiit.ac.in", Role.FACULTY_STAFF, default_pwd_hash, "CSE", "+91 9876543210"),
        create_user_instance("COORD-CSE", "Garv Jain", "garv.jain@lnmiit.ac.in", Role.DEPARTMENT_COORDINATOR, default_pwd_hash, "CSE", "+91 9876543211"),
        create_user_instance("MEM-IQAC", "Shivam Sharma", "shivam.sharma@lnmiit.ac.in", Role.IQAC_MEMBER, default_pwd_hash, "ECE", "+91 9876543212"),
        create_user_instance("COORD-IQAC", "Manas Gupta", "manas.gupta@lnmiit.ac.in", Role.IQAC_COORDINATOR, default_pwd_hash, "CSE", "+91 9876543213"),
        create_user_instance("ADMIN-01", "System Administrator", "admin@lnmiit.ac.in", Role.ADMINISTRATOR, default_pwd_hash, "CSE", "+91 9876543214"),
        create_user_instance("student01", "Dipanshu Soni", "dipanshu.soni@lnmiit.ac.in", Role.STUDENT, default_pwd_hash, "ECE", "+91 9876543215"),
    ]
    for u in users:
        user_repo.save(u)

    # 4. Activities (surface level)
    activities = [
        Activity(
            activityId="ACT-0142",
            title="Feedback Analysis Report",
            deadline="2026-11-20",
            priority=Priority.HIGH,
            status=ActivityStatus.SUBMITTED,
            outcome="Feedback summary prepared and analyzed across all academic sections.",
            domainId="CRITERION-2",
            departmentId="CSE",
            createdBy="COORD-CSE",
            assignedTo="staff01",
            description="Collect and analyze undergraduate course feedback."
        ),
        Activity(
            activityId="ACT-0150",
            title="Faculty Development Workshop",
            deadline="2026-11-05",
            priority=Priority.MEDIUM,
            status=ActivityStatus.ASSIGNED,
            outcome="",
            domainId="CRITERION-3",
            departmentId="CSE",
            createdBy="COORD-CSE",
            assignedTo="staff01",
            description="Organize 2-day workshop on modern software engineering practices."
        ),
        Activity(
            activityId="ACT-0131",
            title="Academic Audit Summary",
            deadline="2026-10-10",
            priority=Priority.HIGH,
            status=ActivityStatus.RETURNED,
            outcome="Preliminary course file audit completed.",
            domainId="CRITERION-1",
            departmentId="CSE",
            createdBy="COORD-CSE",
            assignedTo="staff01",
            description="Internal departmental course file review."
        ),
        Activity(
            activityId="ACT-0138",
            title="VLSI Design Laboratory Audit",
            deadline="2026-11-15",
            priority=Priority.MEDIUM,
            status=ActivityStatus.SUBMITTED,
            outcome="Equipment verification complete.",
            domainId="CRITERION-4",
            departmentId="ECE",
            createdBy="COORD-IQAC",
            assignedTo="MEM-IQAC",
            description="Audit lab hardware and safety certifications."
        )
    ]
    for a in activities:
        activity_repo.save(a)

    # 5. Create sample dummy file on disk for EV-0091
    upload_dir = Path(Config.UPLOAD_FOLDER)
    upload_dir.mkdir(parents=True, exist_ok=True)
    sample_path = upload_dir / "feedback_summary.pdf"
    if not sample_path.exists():
        with open(sample_path, "wb") as f:
            f.write(b"%PDF-1.4\n% Sample Evidence Document for IQAC System\n")

    sample_ev = Evidence(
        evidenceId="EV-0091",
        activityId="ACT-0142",
        fileName="feedback_summary.pdf",
        fileType="PDF",
        fileSize=10240,
        filePath=str(sample_path),
        uploadedBy="staff01",
        description="Consolidated student feedback survey summary",
        verificationStatus=VerificationStatus.PENDING
    )
    evidence_repo.save(sample_ev)

    # 6. Sample Notifications
    notifs = [
        Notification("NOTIF-101", "staff01", "You have been assigned to activity: Feedback Analysis Report", "ASSIGNMENT", "2026-10-20T10:00:00"),
        Notification("NOTIF-102", "COORD-CSE", "Evidence uploaded for 'Feedback Analysis Report'", "VERIFICATION", "2026-10-22T14:30:00"),
        Notification("NOTIF-103", "staff01", "Activity 'Academic Audit Summary' returned for rework: Please attach student survey breakdowns.", "RETURN", "2026-10-25T11:15:00")
    ]
    for n in notifs:
        notif_repo.save(n)

    # 7. Sample History Logs (SRS Section 36 Object Diagram & Table 27)
    history_logs = [
        ActivityHistoryLog("LOG-2210", "ACT-0142", "COORD-CSE", "Created", None, "CREATED", "2026-09-15 10:00:00"),
        ActivityHistoryLog("LOG-2211", "ACT-0142", "staff01", "STATUS_UPDATED", "ASSIGNED", "IN_PROGRESS", "2026-09-16 11:20:00"),
        ActivityHistoryLog("LOG-2212", "ACT-0142", "staff01", "Evidence Uploaded", None, "feedback_summary.pdf (EV-0091)", "2026-09-18 11:42:00"),
        ActivityHistoryLog("LOG-2213", "ACT-0142", "staff01", "SUBMITTED_FOR_VERIFICATION", "EVIDENCE_UPLOADED", "SUBMITTED", "2026-09-20 09:15:00"),
        ActivityHistoryLog("LOG-2214", "ACT-0131", "COORD-CSE", "Created", None, "CREATED", "2026-10-01 09:00:00"),
        ActivityHistoryLog("LOG-2215", "ACT-0131", "MEM-IQAC", "RETURNED", "SUBMITTED", "RETURNED: Please attach student survey breakdowns.", "2026-10-25 11:15:00")
    ]
    for h in history_logs:
        history_repo.save(h)

    # 8. Sample Feedback Forms (FR-036 - FR-040, UC-018)
    feedback_repo = FeedbackRepository()
    sample_form = FeedbackForm(
        formId="FB-1001",
        title="Student Curriculum & Laboratory Feedback 2026",
        activityId="ACT-0142",
        targetRole="STUDENT",
        isOpen=True,
        createdBy="COORD-IQAC",
        opensAt="2026-01-01",
        closesAt="2026-12-31"
    )
    feedback_repo.saveForm(sample_form)

    print("Database seeded with departments, criteria, users, activities, evidence, notifications, history logs, and feedback forms!")

if __name__ == "__main__":
    seed_database()
