"""Reporting service - business logic for reports, dashboards, and KPIs"""

import csv
import io
import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session, joinedload

from addons.agcm_reporting.models.report_definition import (
    ReportDefinition, ReportSchedule, ReportFormat,
)
from addons.agcm_reporting.models.dashboard_widget import (
    DashboardLayout, DashboardWidget,
)
from addons.agcm_reporting.schemas.report_definition import (
    ReportDefinitionCreate, ReportDefinitionUpdate,
    ReportScheduleCreate, ReportScheduleUpdate,
)
from addons.agcm_reporting.schemas.dashboard_widget import (
    DashboardLayoutCreate, DashboardLayoutUpdate,
    DashboardWidgetCreate, DashboardWidgetUpdate,
)

logger = logging.getLogger(__name__)

# Supported data sources for reports
DATA_SOURCE_TABLES = {
    "projects": "agcm_projects",
    "daily_logs": "agcm_daily_activity_logs",
    "manpower": "agcm_manpower",
    "inspections": "agcm_inspections",
    "accidents": "agcm_accidents",
    "visitors": "agcm_visitors",
    "safety_violations": "agcm_safety_violations",
    "delays": "agcm_delays",
    "deficiencies": "agcm_deficiencies",
}


class ReportingService:
    """Handles report definitions, dashboards, and KPI calculations."""

    def __init__(self, db: Session, company_id: int, user_id: int):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id

    # =========================================================================
    # REPORT DEFINITIONS
    # =========================================================================

    def list_reports(
        self,
        page: int = 1,
        page_size: int = 20,
        report_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict:
        """List report definitions with pagination."""
        page_size = min(page_size, 200)
        query = (
            self.db.query(ReportDefinition)
            .options(joinedload(ReportDefinition.schedules))
            .filter(ReportDefinition.company_id == self.company_id)
        )

        if report_type:
            query = query.filter(ReportDefinition.report_type == report_type)
        if search:
            term = f"%{search}%"
            query = query.filter(
                (ReportDefinition.name.ilike(term))
                | (ReportDefinition.description.ilike(term))
            )

        # Show shared reports or user's own
        query = query.filter(
            (ReportDefinition.is_shared == True)
            | (ReportDefinition.created_by == self.user_id)
        )

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(ReportDefinition.id.desc()).offset(skip).limit(page_size).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_report(self, report_id: int) -> Optional[ReportDefinition]:
        """Get a single report definition."""
        return (
            self.db.query(ReportDefinition)
            .options(joinedload(ReportDefinition.schedules))
            .filter(
                ReportDefinition.id == report_id,
                ReportDefinition.company_id == self.company_id,
            )
            .first()
        )

    def create_report(self, data: ReportDefinitionCreate) -> ReportDefinition:
        """Create a report definition."""
        report = ReportDefinition(
            company_id=self.company_id,
            name=data.name,
            description=data.description,
            report_type=data.report_type,
            data_source=data.data_source,
            columns=data.columns,
            filters=data.filters,
            sort_by=data.sort_by,
            sort_order=data.sort_order,
            group_by=data.group_by,
            is_system=False,
            is_shared=data.is_shared,
            created_by=self.user_id,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def update_report(self, report_id: int, data: ReportDefinitionUpdate) -> Optional[ReportDefinition]:
        """Update a report definition."""
        report = self.get_report(report_id)
        if not report:
            return None
        if report.is_system:
            return None  # Cannot edit system reports

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(report, key, value)
        report.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(report)
        return report

    def delete_report(self, report_id: int) -> bool:
        """Delete a report definition."""
        report = self.get_report(report_id)
        if not report or report.is_system:
            return False
        self.db.delete(report)
        self.db.commit()
        return True

    def execute_report(self, report_id: int, filters: Optional[dict] = None) -> dict:
        """Execute a report and return data."""
        report = self.get_report(report_id)
        if not report:
            return {"error": "Report not found", "rows": [], "columns": []}

        table_name = DATA_SOURCE_TABLES.get(report.data_source)
        if not table_name:
            return {"error": f"Unknown data source: {report.data_source}", "rows": [], "columns": []}

        try:
            # Build simple query
            base_query = f"SELECT * FROM {table_name} WHERE company_id = :company_id"
            params: Dict[str, Any] = {"company_id": self.company_id}

            # Apply saved filters
            saved_filters = {}
            if report.filters:
                try:
                    saved_filters = json.loads(report.filters)
                except (json.JSONDecodeError, TypeError):
                    pass

            # Merge with runtime filters
            merged_filters = {**saved_filters, **(filters or {})}

            if "project_id" in merged_filters and merged_filters["project_id"]:
                base_query += " AND project_id = :project_id"
                params["project_id"] = merged_filters["project_id"]

            if "date_from" in merged_filters and merged_filters["date_from"]:
                base_query += " AND created_at >= :date_from"
                params["date_from"] = merged_filters["date_from"]

            if "date_to" in merged_filters and merged_filters["date_to"]:
                base_query += " AND created_at <= :date_to"
                params["date_to"] = merged_filters["date_to"]

            # Sort — whitelist column names to prevent SQL injection
            if report.sort_by:
                import re as _re
                if _re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', report.sort_by):
                    direction = "DESC" if report.sort_order == "desc" else "ASC"
                    base_query += f" ORDER BY {report.sort_by} {direction}"
                else:
                    base_query += " ORDER BY id DESC"
            else:
                base_query += " ORDER BY id DESC"

            base_query += " LIMIT 1000"

            result = self.db.execute(text(base_query), params)
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]

            # Parse column definitions
            report_columns = []
            if report.columns:
                try:
                    report_columns = json.loads(report.columns)
                except (json.JSONDecodeError, TypeError):
                    report_columns = [{"key": c, "title": c.replace("_", " ").title()} for c in columns]
            else:
                report_columns = [{"key": c, "title": c.replace("_", " ").title()} for c in columns]

            return {
                "columns": report_columns,
                "rows": rows,
                "total": len(rows),
                "report_name": report.name,
            }
        except Exception as e:
            logger.error(f"Failed to execute report {report_id}: {e}")
            return {"error": str(e), "rows": [], "columns": []}

    def export_report(self, report_id: int, format: str = "csv", filters: Optional[dict] = None) -> Optional[tuple]:
        """Export report data as CSV/Excel bytes. Returns (bytes, content_type, filename)."""
        data = self.execute_report(report_id, filters)
        if "error" in data and data["error"]:
            return None

        report = self.get_report(report_id)
        if not report:
            return None

        rows = data.get("rows", [])
        col_defs = data.get("columns", [])
        col_keys = [c.get("key", c) if isinstance(c, dict) else c for c in col_defs]
        col_titles = [c.get("title", c.get("key", "")) if isinstance(c, dict) else c for c in col_defs]

        if format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(col_titles)
            for row in rows:
                writer.writerow([row.get(k, "") for k in col_keys])
            content = output.getvalue().encode("utf-8")
            return content, "text/csv", f"{report.name}.csv"

        # Default: return as CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(col_titles)
        for row in rows:
            writer.writerow([row.get(k, "") for k in col_keys])
        content = output.getvalue().encode("utf-8")
        return content, "text/csv", f"{report.name}.csv"

    # =========================================================================
    # REPORT SCHEDULES
    # =========================================================================

    def create_schedule(self, report_id: int, data: ReportScheduleCreate) -> Optional[ReportSchedule]:
        """Add a schedule to a report."""
        report = self.get_report(report_id)
        if not report:
            return None

        schedule = ReportSchedule(
            report_id=report_id,
            company_id=self.company_id,
            schedule_type=data.schedule_type,
            recipients=data.recipients,
            is_active=data.is_active,
            format=data.format,
        )
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        return schedule

    def update_schedule(self, schedule_id: int, data: ReportScheduleUpdate) -> Optional[ReportSchedule]:
        """Update a report schedule."""
        schedule = (
            self.db.query(ReportSchedule)
            .filter(
                ReportSchedule.id == schedule_id,
                ReportSchedule.company_id == self.company_id,
            )
            .first()
        )
        if not schedule:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(schedule, key, value)

        self.db.commit()
        self.db.refresh(schedule)
        return schedule

    def delete_schedule(self, schedule_id: int) -> bool:
        """Delete a report schedule."""
        schedule = (
            self.db.query(ReportSchedule)
            .filter(
                ReportSchedule.id == schedule_id,
                ReportSchedule.company_id == self.company_id,
            )
            .first()
        )
        if not schedule:
            return False
        self.db.delete(schedule)
        self.db.commit()
        return True

    # =========================================================================
    # DASHBOARD LAYOUTS
    # =========================================================================

    def list_layouts(
        self,
        page: int = 1,
        page_size: int = 20,
        layout_type: Optional[str] = None,
    ) -> dict:
        """List dashboard layouts."""
        page_size = min(page_size, 200)
        query = (
            self.db.query(DashboardLayout)
            .options(joinedload(DashboardLayout.widgets))
            .filter(DashboardLayout.company_id == self.company_id)
        )

        if layout_type:
            query = query.filter(DashboardLayout.layout_type == layout_type)

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(DashboardLayout.id.desc()).offset(skip).limit(page_size).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_layout(self, layout_id: int) -> Optional[DashboardLayout]:
        """Get a dashboard layout with widgets."""
        return (
            self.db.query(DashboardLayout)
            .options(joinedload(DashboardLayout.widgets))
            .filter(
                DashboardLayout.id == layout_id,
                DashboardLayout.company_id == self.company_id,
            )
            .first()
        )

    def get_default_layout(self, layout_type: str = "executive") -> Optional[DashboardLayout]:
        """Get the default layout for a type."""
        return (
            self.db.query(DashboardLayout)
            .options(joinedload(DashboardLayout.widgets))
            .filter(
                DashboardLayout.company_id == self.company_id,
                DashboardLayout.layout_type == layout_type,
                DashboardLayout.is_default == True,
            )
            .first()
        )

    def create_layout(self, data: DashboardLayoutCreate) -> DashboardLayout:
        """Create a dashboard layout with optional inline widgets."""
        layout = DashboardLayout(
            company_id=self.company_id,
            name=data.name,
            layout_type=data.layout_type,
            is_default=data.is_default,
            created_by=self.user_id,
        )
        self.db.add(layout)
        self.db.flush()

        for w_data in (data.widgets or []):
            widget = DashboardWidget(
                layout_id=layout.id,
                company_id=self.company_id,
                widget_type=w_data.widget_type,
                title=w_data.title,
                config=w_data.config,
                data_source=w_data.data_source,
                position_x=w_data.position_x,
                position_y=w_data.position_y,
                width=w_data.width,
                height=w_data.height,
                display_order=w_data.display_order,
            )
            self.db.add(widget)

        self.db.commit()
        self.db.refresh(layout)
        return layout

    def update_layout(self, layout_id: int, data: DashboardLayoutUpdate) -> Optional[DashboardLayout]:
        """Update a dashboard layout."""
        layout = self.get_layout(layout_id)
        if not layout:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(layout, key, value)
        layout.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(layout)
        return layout

    def delete_layout(self, layout_id: int) -> bool:
        """Delete a dashboard layout."""
        layout = self.get_layout(layout_id)
        if not layout:
            return False
        self.db.delete(layout)
        self.db.commit()
        return True

    # =========================================================================
    # DASHBOARD WIDGETS
    # =========================================================================

    def create_widget(self, layout_id: int, data: DashboardWidgetCreate) -> Optional[DashboardWidget]:
        """Add a widget to a layout."""
        layout = self.get_layout(layout_id)
        if not layout:
            return None

        widget = DashboardWidget(
            layout_id=layout_id,
            company_id=self.company_id,
            widget_type=data.widget_type,
            title=data.title,
            config=data.config,
            data_source=data.data_source,
            position_x=data.position_x,
            position_y=data.position_y,
            width=data.width,
            height=data.height,
            display_order=data.display_order,
        )
        self.db.add(widget)
        self.db.commit()
        self.db.refresh(widget)
        return widget

    def update_widget(self, widget_id: int, data: DashboardWidgetUpdate) -> Optional[DashboardWidget]:
        """Update a widget."""
        widget = (
            self.db.query(DashboardWidget)
            .filter(
                DashboardWidget.id == widget_id,
                DashboardWidget.company_id == self.company_id,
            )
            .first()
        )
        if not widget:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(widget, key, value)

        self.db.commit()
        self.db.refresh(widget)
        return widget

    def delete_widget(self, widget_id: int) -> bool:
        """Delete a widget."""
        widget = (
            self.db.query(DashboardWidget)
            .filter(
                DashboardWidget.id == widget_id,
                DashboardWidget.company_id == self.company_id,
            )
            .first()
        )
        if not widget:
            return False
        self.db.delete(widget)
        self.db.commit()
        return True

    # =========================================================================
    # KPI ENDPOINTS
    # =========================================================================

    def get_portfolio_kpis(self) -> dict:
        """Get portfolio-level KPIs across all projects."""
        try:
            # Total projects
            total_projects = self.db.execute(
                text("SELECT COUNT(*) FROM agcm_projects WHERE company_id = :cid"),
                {"cid": self.company_id},
            ).scalar() or 0

            # Active projects
            active_projects = self.db.execute(
                text("SELECT COUNT(*) FROM agcm_projects WHERE company_id = :cid AND status = 'inprogress'"),
                {"cid": self.company_id},
            ).scalar() or 0

            # Completed projects
            completed_projects = self.db.execute(
                text("SELECT COUNT(*) FROM agcm_projects WHERE company_id = :cid AND status = 'completed'"),
                {"cid": self.company_id},
            ).scalar() or 0

            # Total daily logs
            total_logs = self.db.execute(
                text("SELECT COUNT(*) FROM agcm_daily_activity_logs WHERE company_id = :cid"),
                {"cid": self.company_id},
            ).scalar() or 0

            # Total accidents
            total_accidents = self.db.execute(
                text("SELECT COUNT(*) FROM agcm_accidents WHERE company_id = :cid"),
                {"cid": self.company_id},
            ).scalar() or 0

            # Total deficiencies
            total_deficiencies = self.db.execute(
                text("SELECT COUNT(*) FROM agcm_deficiencies WHERE company_id = :cid"),
                {"cid": self.company_id},
            ).scalar() or 0

            return {
                "total_projects": total_projects,
                "active_projects": active_projects,
                "completed_projects": completed_projects,
                "total_daily_logs": total_logs,
                "total_accidents": total_accidents,
                "total_deficiencies": total_deficiencies,
                "completion_rate": round(
                    (completed_projects / total_projects * 100) if total_projects > 0 else 0, 1
                ),
            }
        except Exception as e:
            logger.error(f"Failed to get portfolio KPIs: {e}")
            return {
                "total_projects": 0, "active_projects": 0, "completed_projects": 0,
                "total_daily_logs": 0, "total_accidents": 0, "total_deficiencies": 0,
                "completion_rate": 0,
            }

    def get_project_kpis(self, project_id: int) -> dict:
        """Get project-level KPIs."""
        try:
            params = {"cid": self.company_id, "pid": project_id}

            total_logs = self.db.execute(
                text("SELECT COUNT(*) FROM agcm_daily_activity_logs WHERE company_id = :cid AND project_id = :pid"),
                params,
            ).scalar() or 0

            total_inspections = self.db.execute(
                text("""
                    SELECT COUNT(*) FROM agcm_inspections i
                    JOIN agcm_daily_activity_logs d ON i.daily_activity_log_id = d.id
                    WHERE d.company_id = :cid AND d.project_id = :pid
                """),
                params,
            ).scalar() or 0

            total_accidents = self.db.execute(
                text("""
                    SELECT COUNT(*) FROM agcm_accidents a
                    JOIN agcm_daily_activity_logs d ON a.daily_activity_log_id = d.id
                    WHERE d.company_id = :cid AND d.project_id = :pid
                """),
                params,
            ).scalar() or 0

            total_deficiencies = self.db.execute(
                text("""
                    SELECT COUNT(*) FROM agcm_deficiencies df
                    JOIN agcm_daily_activity_logs d ON df.daily_activity_log_id = d.id
                    WHERE d.company_id = :cid AND d.project_id = :pid
                """),
                params,
            ).scalar() or 0

            total_delays = self.db.execute(
                text("""
                    SELECT COUNT(*) FROM agcm_delays dl
                    JOIN agcm_daily_activity_logs d ON dl.daily_activity_log_id = d.id
                    WHERE d.company_id = :cid AND d.project_id = :pid
                """),
                params,
            ).scalar() or 0

            total_violations = self.db.execute(
                text("""
                    SELECT COUNT(*) FROM agcm_safety_violations sv
                    JOIN agcm_daily_activity_logs d ON sv.daily_activity_log_id = d.id
                    WHERE d.company_id = :cid AND d.project_id = :pid
                """),
                params,
            ).scalar() or 0

            return {
                "total_daily_logs": total_logs,
                "total_inspections": total_inspections,
                "total_accidents": total_accidents,
                "total_deficiencies": total_deficiencies,
                "total_delays": total_delays,
                "total_safety_violations": total_violations,
                "safety_score": max(0, 100 - (total_accidents * 10) - (total_violations * 5)),
            }
        except Exception as e:
            logger.error(f"Failed to get project KPIs: {e}")
            return {
                "total_daily_logs": 0, "total_inspections": 0, "total_accidents": 0,
                "total_deficiencies": 0, "total_delays": 0, "total_safety_violations": 0,
                "safety_score": 100,
            }

    def get_financial_summary(self, project_id: int) -> dict:
        """Get financial summary for a project. Placeholder for budget integration."""
        return {
            "project_id": project_id,
            "budgeted": 0,
            "committed": 0,
            "actual": 0,
            "forecast": 0,
            "variance": 0,
            "percent_spent": 0,
        }
