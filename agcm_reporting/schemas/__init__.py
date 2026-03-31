"""AGCM Reporting Schemas"""

from addons.agcm_reporting.schemas.report_definition import (
    ReportDefinitionCreate, ReportDefinitionUpdate, ReportDefinitionResponse,
    ReportScheduleCreate, ReportScheduleUpdate, ReportScheduleResponse,
)
from addons.agcm_reporting.schemas.dashboard_widget import (
    DashboardLayoutCreate, DashboardLayoutUpdate, DashboardLayoutResponse,
    DashboardWidgetCreate, DashboardWidgetUpdate, DashboardWidgetResponse,
)

__all__ = [
    "ReportDefinitionCreate", "ReportDefinitionUpdate", "ReportDefinitionResponse",
    "ReportScheduleCreate", "ReportScheduleUpdate", "ReportScheduleResponse",
    "DashboardLayoutCreate", "DashboardLayoutUpdate", "DashboardLayoutResponse",
    "DashboardWidgetCreate", "DashboardWidgetUpdate", "DashboardWidgetResponse",
]
