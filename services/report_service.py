import io
import csv
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from repositories.activity_repository import ActivityRepository
from repositories.department_repository import DomainAreaRepository
from models.enums import ActivityStatus
from models.activity import Activity

class ReportService:
    """
    FR-046 - FR-050 & UC-016, UC-017: Activity & Quality Reporting Service.
    Generates department-wise and domain-wise aggregated reports with strict verification
    counting rules (BR-006: only verified activities count towards verified quality accomplishment).
    Groups reports criterion-wise (FR-048) and exports in CSV format (FR-049).
    """
    def __init__(
        self,
        activity_repo: Optional[ActivityRepository] = None,
        domain_repo: Optional[DomainAreaRepository] = None
    ):
        self.activity_repo = activity_repo or ActivityRepository()
        self.domain_repo = domain_repo or DomainAreaRepository()

    def _compute_group_summary(self, acts: List[Activity]) -> Dict[str, int]:
        """Computes summary metrics for a collection of activities (FR-050, BR-006)."""
        return {
            "total": len(acts),
            "pending": sum(1 for a in acts if a.status in [ActivityStatus.PLANNED, ActivityStatus.ASSIGNED]),
            "ongoing": sum(1 for a in acts if a.status in [ActivityStatus.IN_PROGRESS, ActivityStatus.EVIDENCE_UPLOADED, ActivityStatus.RETURNED]),
            "completed": sum(1 for a in acts if a.status in [ActivityStatus.COMPLETED, ActivityStatus.SUBMITTED]),
            "verified": sum(1 for a in acts if a.status == ActivityStatus.VERIFIED),  # BR-006
            "overdue": sum(1 for a in acts if a.isOverdue()),
            "in_progress": sum(1 for a in acts if a.status in [ActivityStatus.ASSIGNED, ActivityStatus.IN_PROGRESS, ActivityStatus.EVIDENCE_UPLOADED]),
            "submitted": sum(1 for a in acts if a.status == ActivityStatus.SUBMITTED),
            "returned": sum(1 for a in acts if a.status == ActivityStatus.RETURNED),
            "cancelled": sum(1 for a in acts if a.status == ActivityStatus.CANCELLED),
        }

    def generateReport(
        self,
        departmentId: Optional[str] = None,
        domainId: Optional[str] = None,
        startDate: Optional[str] = None,
        endDate: Optional[str] = None
    ) -> Dict[str, Any]:
        all_activities = self.activity_repo.findAll()

        filtered = []
        for act in all_activities:
            if departmentId and departmentId != "All" and act.departmentId != departmentId:
                continue
            if domainId and domainId != "All" and act.domainId != domainId:
                continue
            if startDate and act.deadline < startDate:
                continue
            if endDate and act.deadline > endDate:
                continue
            filtered.append(act)

        # Compute overall summary metrics adhering strictly to BR-006 and FR-050
        summary = self._compute_group_summary(filtered)

        # Build Domain Areas mapping (FR-048)
        all_domains = self.domain_repo.findAll()
        domain_names = {d.domainId: d.name for d in all_domains}

        # Group activities by Criterion / Domain (FR-048)
        grouped_dict: Dict[str, List[Activity]] = {}
        for act in filtered:
            dom_id = act.domainId if act.domainId else "UNCATEGORIZED"
            if dom_id not in grouped_dict:
                grouped_dict[dom_id] = []
            grouped_dict[dom_id].append(act)

        criterion_groups = []
        # First iterate over known domains in configured order
        for d in all_domains:
            if d.domainId in grouped_dict:
                acts = grouped_dict[d.domainId]
                criterion_groups.append({
                    "domainId": d.domainId,
                    "domainName": d.name,
                    "activities": acts,
                    "summary": self._compute_group_summary(acts)
                })

        # Add any other domains not in the known domain repository list
        for dom_id, acts in grouped_dict.items():
            if not any(g["domainId"] == dom_id for g in criterion_groups):
                name = domain_names.get(dom_id, "General / Uncategorized" if dom_id == "UNCATEGORIZED" else dom_id)
                criterion_groups.append({
                    "domainId": dom_id,
                    "domainName": name,
                    "activities": acts,
                    "summary": self._compute_group_summary(acts)
                })

        return {
            "summary": summary,
            "activities": filtered,
            "criterion_groups": criterion_groups,
            "filters": {
                "departmentId": departmentId or "All",
                "domainId": domainId or "All",
                "startDate": startDate or "",
                "endDate": endDate or ""
            }
        }

    def exportReportToCsv(self, report_data: Dict[str, Any]) -> str:
        """FR-049: Export generated report to CSV format with criterion-wise grouping."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header summary
        writer.writerow(["IQAC Quality Activity Report"])
        writer.writerow(["Generated At", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(["Department Filter", report_data["filters"]["departmentId"]])
        writer.writerow(["Criterion Domain Filter", report_data["filters"]["domainId"]])
        writer.writerow(["Deadline From", report_data["filters"].get("startDate", "") or "Any"])
        writer.writerow(["Deadline To", report_data["filters"].get("endDate", "") or "Any"])
        writer.writerow([])

        # Summary KPIs
        summary = report_data["summary"]
        writer.writerow(["--- Overall Performance Metrics (FR-050, BR-006) ---"])
        writer.writerow(["Total Activities", summary["total"]])
        writer.writerow(["Pending", summary["pending"]])
        writer.writerow(["Ongoing", summary["ongoing"]])
        writer.writerow(["In Progress", summary["in_progress"]])
        writer.writerow(["Submitted for Verification", summary["submitted"]])
        writer.writerow(["Completed (Awaiting IQAC Review)", summary["completed"]])
        writer.writerow(["Verified (Approved - BR-006)", summary["verified"]])
        writer.writerow(["Returned for Rework", summary["returned"]])
        writer.writerow(["Cancelled", summary["cancelled"]])
        writer.writerow(["Overdue Count", summary["overdue"]])
        writer.writerow([])

        # Criterion-wise Grouping (FR-048)
        criterion_groups = report_data.get("criterion_groups", [])
        if criterion_groups:
            for group in criterion_groups:
                writer.writerow([f"=== Quality Criterion: {group['domainId']} - {group['domainName']} ==="])
                g_sum = group["summary"]
                writer.writerow([
                    "Criterion Summary",
                    f"Total: {g_sum['total']}",
                    f"Pending: {g_sum['pending']}",
                    f"Ongoing: {g_sum['ongoing']}",
                    f"Completed: {g_sum['completed']}",
                    f"Verified: {g_sum['verified']}",
                    f"Overdue: {g_sum['overdue']}"
                ])
                writer.writerow(["Activity ID", "Title", "Department", "Criterion", "Deadline", "Priority", "Status", "Assignee", "Outcome"])
                for act in group["activities"]:
                    writer.writerow([
                        act.activityId,
                        act.title,
                        act.departmentId,
                        group["domainId"],
                        act.deadline,
                        act.priority.value,
                        act.status.value,
                        act.assignedTo or "Unassigned",
                        act.outcome or ""
                    ])
                writer.writerow([])
        else:
            writer.writerow(["No activities match the selected filter criteria."])

        return output.getvalue()
