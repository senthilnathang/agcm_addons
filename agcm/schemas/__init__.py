"""AG CM Schemas"""

from addons.agcm.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetail,
)
from addons.agcm.schemas.daily_activity_log import (
    DailyActivityLogCreate, DailyActivityLogUpdate,
    DailyActivityLogResponse, DailyActivityLogDetail,
    MakeLogRequest,
    ManPowerCreate, ManPowerUpdate, ManPowerResponse,
    NotesCreate, NotesUpdate, NotesResponse,
    InspectionCreate, InspectionUpdate, InspectionResponse,
    AccidentCreate, AccidentUpdate, AccidentResponse,
    VisitorCreate, VisitorUpdate, VisitorResponse,
    SafetyViolationCreate, SafetyViolationUpdate, SafetyViolationResponse,
    DelayCreate, DelayUpdate, DelayResponse,
    DeficiencyCreate, DeficiencyUpdate, DeficiencyResponse,
    PhotoCreate, PhotoUpdate, PhotoResponse,
    WeatherForecastResponse,
)
