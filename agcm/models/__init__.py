"""AG CM Models"""

from addons.agcm.models.lookups import (
    Trade,
    InspectionType,
    AccidentType,
    ViolationType,
)
from addons.agcm.models.project import (
    Project,
    ProjectStatus,
    ProjectOffice,
    agcm_project_contractors,
    agcm_project_users,
)
from addons.agcm.models.daily_activity_log import DailyActivityLog
from addons.agcm.models.manpower import ManPower
from addons.agcm.models.weather import (
    Weather,
    WeatherForecast,
    ClimateType,
    TemperatureUnit,
    WEATHER_CODE_MAP,
)
from addons.agcm.models.notes import Notes
from addons.agcm.models.inspection import Inspection
from addons.agcm.models.accident import Accident
from addons.agcm.models.visitor import Visitor
from addons.agcm.models.safety_violation import SafetyViolation
from addons.agcm.models.delay import Delay
from addons.agcm.models.deficiency import Deficiency
from addons.agcm.models.photo import Photo
from addons.agcm.models.entity_attachment import agcm_entity_attachments
from addons.agcm.models.comment import EntityComment

__all__ = [
    # Lookups
    "Trade",
    "InspectionType",
    "AccidentType",
    "ViolationType",
    # Enums
    "ProjectStatus",
    "ProjectOffice",
    "ClimateType",
    "TemperatureUnit",
    "WEATHER_CODE_MAP",
    # Association tables
    "agcm_project_contractors",
    "agcm_project_users",
    # Core models
    "Project",
    "DailyActivityLog",
    # Child models
    "ManPower",
    "Weather",
    "WeatherForecast",
    "Notes",
    "Inspection",
    "Accident",
    "Visitor",
    "SafetyViolation",
    "Delay",
    "Deficiency",
    "Photo",
    # Generic cross-module
    "agcm_entity_attachments",
    "EntityComment",
]
