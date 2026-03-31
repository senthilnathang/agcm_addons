"""AG CM Safety Schemas"""

from addons.agcm_safety.schemas.checklist import (
    ChecklistTemplateCreate,
    ChecklistTemplateUpdate,
    ChecklistTemplateResponse,
    ChecklistTemplateDetail,
    ChecklistTemplateItemCreate,
    ChecklistTemplateItemResponse,
)
from addons.agcm_safety.schemas.inspection import (
    InspectionCreate,
    InspectionUpdate,
    InspectionResponse,
    InspectionDetail,
    InspectionItemCreate,
    InspectionItemUpdate,
    InspectionItemResponse,
)
from addons.agcm_safety.schemas.punch_list import (
    PunchListItemCreate,
    PunchListItemUpdate,
    PunchListItemResponse,
)
from addons.agcm_safety.schemas.incident import (
    IncidentReportCreate,
    IncidentReportUpdate,
    IncidentReportResponse,
)

__all__ = [
    "ChecklistTemplateCreate",
    "ChecklistTemplateUpdate",
    "ChecklistTemplateResponse",
    "ChecklistTemplateDetail",
    "ChecklistTemplateItemCreate",
    "ChecklistTemplateItemResponse",
    "InspectionCreate",
    "InspectionUpdate",
    "InspectionResponse",
    "InspectionDetail",
    "InspectionItemCreate",
    "InspectionItemUpdate",
    "InspectionItemResponse",
    "PunchListItemCreate",
    "PunchListItemUpdate",
    "PunchListItemResponse",
    "IncidentReportCreate",
    "IncidentReportUpdate",
    "IncidentReportResponse",
]
