from flask import Blueprint, render_template, request, Response, session, flash, redirect, url_for
from routes.auth_routes import login_required, roles_required
from services.report_service import ReportService
from repositories.department_repository import DepartmentRepository, DomainAreaRepository
from models.enums import Role

report_bp = Blueprint("report", __name__)
report_service = ReportService()
dept_repo = DepartmentRepository()
domain_repo = DomainAreaRepository()

@report_bp.route("/reports")
@login_required
@roles_required(Role.DEPARTMENT_COORDINATOR, Role.IQAC_MEMBER, Role.IQAC_COORDINATOR, Role.ADMINISTRATOR)
def view_reports():
    """FR-046 - FR-048, BR-010: View Department and Criterion Reports."""
    user_role = session.get("role")
    user_dept = session.get("department_id")

    department_id = request.args.get("department_id")
    domain_id = request.args.get("domain_id", "All")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    # Restrict Dept Coordinator to their own department
    if user_role == Role.DEPARTMENT_COORDINATOR.value:
        department_id = user_dept
    elif not department_id:
        department_id = "All"

    # Validate date range (C-26)
    if start_date and end_date and start_date > end_date:
        flash("Start date cannot be after end date.", "danger")
        start_date = ""

    report_data = report_service.generateReport(
        departmentId=department_id,
        domainId=domain_id,
        startDate=start_date,
        endDate=end_date
    )

    departments = dept_repo.findAll()
    domains = domain_repo.findAll()

    return render_template(
        "reports.html",
        report_data=report_data,
        departments=departments,
        domains=domains,
        user_role=user_role,
        user_dept=user_dept
    )

@report_bp.route("/reports/export")
@login_required
@roles_required(Role.DEPARTMENT_COORDINATOR, Role.IQAC_MEMBER, Role.IQAC_COORDINATOR, Role.ADMINISTRATOR)
def export_report():
    """FR-049: Export generated reports in CSV file format."""
    user_role = session.get("role")
    user_dept = session.get("department_id")

    department_id = request.args.get("department_id")
    if user_role == Role.DEPARTMENT_COORDINATOR.value:
        department_id = user_dept
    elif not department_id:
        department_id = "All"

    domain_id = request.args.get("domain_id", "All")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    report_data = report_service.generateReport(
        departmentId=department_id,
        domainId=domain_id,
        startDate=start_date,
        endDate=end_date
    )

    csv_content = report_service.exportReportToCsv(report_data)

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=iqac_quality_report.csv"}
    )
