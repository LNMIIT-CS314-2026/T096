import sqlite3
from typing import Optional, List, Dict
from datetime import datetime, date
from models.activity import Activity
from models.enums import ActivityStatus, Priority
from repositories.database import get_db_connection

class ActivityRepository:
    """Persistence repository for Activity entity (Table 27) at surface level."""

    def save(self, activity: Activity) -> None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO activities (
                activity_id, title, description, domain_id, department_id,
                created_by, assigned_to, planned_start, deadline, priority, status, outcome, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(activity_id) DO UPDATE SET
                title = excluded.title,
                description = excluded.description,
                domain_id = excluded.domain_id,
                department_id = excluded.department_id,
                assigned_to = excluded.assigned_to,
                planned_start = excluded.planned_start,
                deadline = excluded.deadline,
                priority = excluded.priority,
                status = excluded.status,
                outcome = excluded.outcome
            """,
            (
                activity.activityId,
                activity.title,
                activity.description,
                activity.domainId if activity.domainId else None,
                activity.departmentId,
                activity.createdBy,
                activity.assignedTo if activity.assignedTo else None,
                activity.plannedStart if activity.plannedStart else None,
                activity.deadline,
                activity.priority.value if hasattr(activity.priority, "value") else str(activity.priority),
                activity.status.value if hasattr(activity.status, "value") else str(activity.status),
                activity.outcome,
                activity.createdAt
            )
        )
        conn.commit()
        conn.close()

    def findById(self, activityId: str) -> Optional[Activity]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM activities WHERE activity_id = ?", (activityId,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return self._row_to_activity(row)

    def findAll(self, status: Optional[str] = None, departmentId: Optional[str] = None) -> List[Activity]:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM activities WHERE 1=1"
        params = []
        if status and status != "All":
            query += " AND status = ?"
            params.append(status)
        if departmentId and departmentId != "All":
            query += " AND department_id = ?"
            params.append(departmentId)
        query += " ORDER BY deadline ASC"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_activity(r) for r in rows]

    def findByAssignee(self, userId: str) -> List[Activity]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM activities WHERE assigned_to = ? ORDER BY deadline ASC", (userId,))
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_activity(r) for r in rows]

    def updateStatus(self, activityId: str, status: ActivityStatus | str) -> None:
        conn = get_db_connection()
        cursor = conn.cursor()
        status_str = status.value if hasattr(status, "value") else str(status)
        cursor.execute("UPDATE activities SET status = ? WHERE activity_id = ?", (status_str, activityId))
        conn.commit()
        conn.close()

    def recordOutcome(self, activityId: str, outcome: str) -> None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE activities SET outcome = ? WHERE activity_id = ?", (outcome.strip(), activityId))
        conn.commit()
        conn.close()

    def getDashboardCountsForDept(self, departmentId: str) -> Dict[str, int]:
        """
        Dept-scoped KPI counts for Department Coordinators (FR-050).
        Same 5-category structure but filtered to one department.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT activity_id, status, deadline FROM activities WHERE department_id = ?", (departmentId,))
        rows = cursor.fetchall()
        conn.close()
        return self._compute_counts(rows)

    def getDashboardCountsForAssignee(self, userId: str) -> Dict[str, int]:
        """
        User-scoped KPI counts for Faculty/Staff assigned activities (FR-050).
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT activity_id, status, deadline FROM activities WHERE assigned_to = ?", (userId,))
        rows = cursor.fetchall()
        conn.close()
        return self._compute_counts(rows)

    def getDashboardCounts(
        self,
        role: Optional[str] = None,
        departmentId: Optional[str] = None,
        userId: Optional[str] = None
    ) -> Optional[Dict[str, int]]:
        """
        Role- and department-scoped dashboard KPI counts (FR-050).
        - STUDENT: returns None (students do not track faculty activities).
        - FACULTY_STAFF: returns counts for activities assigned to this user.
        - DEPARTMENT_COORDINATOR: returns counts for activities in the user's department.
        - IQAC / Admin (or no filter): returns institution-wide counts.
        """
        from models.enums import Role as _Role

        role_val = role.value if hasattr(role, "value") else str(role or "")
        if role_val == _Role.STUDENT.value:
            return None

        if role_val == _Role.FACULTY_STAFF.value or (userId and not role_val and not departmentId):
            return self.getDashboardCountsForAssignee(userId or "")

        if role_val == _Role.DEPARTMENT_COORDINATOR.value or (departmentId and not role_val):
            return self.getDashboardCountsForDept(departmentId or "")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT activity_id, status, deadline FROM activities")
        rows = cursor.fetchall()
        conn.close()
        return self._compute_counts(rows)

    def _compute_counts(self, rows) -> Dict[str, int]:
        """Shared count computation for the 5 SRS FR-050 categories."""
        counts = {
            "total": len(rows),
            "pending": 0,
            "ongoing": 0,
            "completed": 0,
            "overdue": 0,
            "verified": 0,
            # Aliases for backwards-compat
            "in_progress": 0,
            "submitted": 0,
            "returned": 0
        }
        today = date.today()
        for r in rows:
            st = r["status"]
            dl_str = r["deadline"]

            # Overdue check (FR-019, BR-009)
            if dl_str and st not in ["VERIFIED", "CANCELLED", "COMPLETED", "SUBMITTED"]:
                try:
                    if datetime.strptime(dl_str[:10], "%Y-%m-%d").date() < today:
                        counts["overdue"] += 1
                except Exception:
                    pass

            if st in ["PLANNED", "ASSIGNED"]:
                counts["pending"] += 1
            elif st in ["IN_PROGRESS", "EVIDENCE_UPLOADED", "RETURNED"]:
                counts["ongoing"] += 1
                if st == "RETURNED":
                    counts["returned"] += 1
                else:
                    counts["in_progress"] += 1
            elif st in ["COMPLETED", "SUBMITTED"]:
                counts["completed"] += 1
                if st == "SUBMITTED":
                    counts["submitted"] += 1
            elif st == "VERIFIED":
                counts["verified"] += 1
        return counts

    def _row_to_activity(self, row: sqlite3.Row) -> Activity:
        planned_start = None
        if "planned_start" in row.keys():
            planned_start = row["planned_start"]
        return Activity(
            activityId=row["activity_id"],
            title=row["title"],
            deadline=row["deadline"],
            priority=row["priority"],
            status=row["status"],
            outcome=row["outcome"] or "",
            domainId=row["domain_id"] or "",
            departmentId=row["department_id"] or "",
            createdBy=row["created_by"] or "",
            assignedTo=row["assigned_to"],
            plannedStart=planned_start,
            description=row["description"] or "",
            createdAt=row["created_at"]
        )
