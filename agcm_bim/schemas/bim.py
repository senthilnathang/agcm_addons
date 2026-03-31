"""Pydantic schemas for BIM module"""

from datetime import date, datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ─── BIM Model ───────────────────────────────────────────────────────────────

class BIMModelCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    discipline: Optional[str] = Field(None, max_length=50)
    file_format: Optional[str] = Field(None, max_length=20)
    project_id: int


class BIMModelUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    discipline: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = None


class BIMModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    project_id: int
    sequence_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    discipline: Optional[str] = None
    file_format: Optional[str] = None
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    status: Optional[str] = None
    version: int = 1
    is_current: bool = True
    parent_model_id: Optional[int] = None
    element_count: int = 0
    processing_error: Optional[str] = None
    uploaded_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BIMModelDetail(BIMModelResponse):
    metadata_json: Optional[str] = None
    viewpoint_count: int = 0
    version_history: List[dict] = []
    element_summary: Optional[dict] = None


# ─── BIM Viewpoint ───────────────────────────────────────────────────────────

class BIMViewpointCreate(BaseModel):
    model_id: int
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    camera_position: Optional[str] = None
    camera_target: Optional[str] = None
    section_planes: Optional[str] = None
    visible_elements: Optional[str] = None
    hidden_elements: Optional[str] = None
    annotations: Optional[str] = None
    screenshot_url: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None


class BIMViewpointUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    camera_position: Optional[str] = None
    camera_target: Optional[str] = None
    section_planes: Optional[str] = None
    visible_elements: Optional[str] = None
    hidden_elements: Optional[str] = None
    annotations: Optional[str] = None
    screenshot_url: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None


class BIMViewpointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    model_id: int
    name: str
    description: Optional[str] = None
    camera_position: Optional[str] = None
    camera_target: Optional[str] = None
    section_planes: Optional[str] = None
    visible_elements: Optional[str] = None
    hidden_elements: Optional[str] = None
    annotations: Optional[str] = None
    screenshot_url: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None


# ─── Clash Test ──────────────────────────────────────────────────────────────

class ClashTestCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    project_id: int
    model_a_id: Optional[int] = None
    model_b_id: Optional[int] = None
    test_type: Optional[str] = "hard"
    tolerance: Optional[float] = 0.01


class ClashTestUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    model_a_id: Optional[int] = None
    model_b_id: Optional[int] = None
    test_type: Optional[str] = None
    tolerance: Optional[float] = None
    notes: Optional[str] = None


class ClashTestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    project_id: int
    sequence_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    model_a_id: Optional[int] = None
    model_b_id: Optional[int] = None
    test_type: str = "hard"
    tolerance: float = 0.01
    status: Optional[str] = None
    total_clashes: int = 0
    critical_count: int = 0
    major_count: int = 0
    minor_count: int = 0
    run_date: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ClashTestDetail(ClashTestResponse):
    model_a_name: Optional[str] = None
    model_b_name: Optional[str] = None
    results: List[dict] = []


# ─── Clash Result ────────────────────────────────────────────────────────────

class ClashResultUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    severity: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    resolution_notes: Optional[str] = None


class ClashResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    clash_test_id: int
    company_id: int
    sequence_name: Optional[str] = None
    element_a_id: Optional[str] = None
    element_a_name: Optional[str] = None
    element_a_type: Optional[str] = None
    element_b_id: Optional[str] = None
    element_b_name: Optional[str] = None
    element_b_type: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    clash_point: Optional[str] = None
    distance: Optional[float] = None
    description: Optional[str] = None
    screenshot_url: Optional[str] = None
    viewpoint_id: Optional[int] = None
    assigned_to: Optional[int] = None
    resolved_by: Optional[int] = None
    resolved_date: Optional[date] = None
    resolution_notes: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ClashResultResolve(BaseModel):
    resolution_notes: Optional[str] = None


class ClashResultAssign(BaseModel):
    assigned_to: int


# ─── BIM Element ─────────────────────────────────────────────────────────────

class BIMElementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    model_id: int
    global_id: str
    ifc_type: str
    name: Optional[str] = None
    description: Optional[str] = None
    properties_json: Optional[str] = None
    material: Optional[str] = None
    level: Optional[str] = None
    discipline: Optional[str] = None
    bounding_box: Optional[str] = None


class BIMModelSummary(BaseModel):
    """Aggregated summary of a model's elements."""
    model_id: int
    element_count: int = 0
    types: Dict[str, int] = {}       # ifc_type -> count
    levels: Dict[str, int] = {}      # level -> count
    materials: Dict[str, int] = {}   # material -> count
    disciplines: Dict[str, int] = {} # discipline -> count


# ─── BIM 3D Annotations ────────────────────────────────────────────────────

class BIMAnnotationCreate(BaseModel):
    project_id: int
    model_id: Optional[int] = None
    world_pos_x: float = 0
    world_pos_y: float = 0
    world_pos_z: float = 0
    eye_x: Optional[float] = None
    eye_y: Optional[float] = None
    eye_z: Optional[float] = None
    look_x: Optional[float] = None
    look_y: Optional[float] = None
    look_z: Optional[float] = None
    up_x: Optional[float] = 0
    up_y: Optional[float] = 1
    up_z: Optional[float] = 0
    entity_id: Optional[str] = None
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    priority: Optional[str] = Field("medium", pattern=r"^(low|medium|high|critical)$")
    status: Optional[str] = Field("open", pattern=r"^(open|in_progress|resolved)$")
    assigned_to: Optional[int] = None
    linked_entity_type: Optional[str] = None
    linked_entity_id: Optional[int] = None


class BIMAnnotationUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    priority: Optional[str] = Field(None, pattern=r"^(low|medium|high|critical)$")
    status: Optional[str] = Field(None, pattern=r"^(open|in_progress|resolved)$")
    assigned_to: Optional[int] = None
    world_pos_x: Optional[float] = None
    world_pos_y: Optional[float] = None
    world_pos_z: Optional[float] = None
    eye_x: Optional[float] = None
    eye_y: Optional[float] = None
    eye_z: Optional[float] = None
    look_x: Optional[float] = None
    look_y: Optional[float] = None
    look_z: Optional[float] = None
    up_x: Optional[float] = None
    up_y: Optional[float] = None
    up_z: Optional[float] = None
    entity_id: Optional[str] = None
    linked_entity_type: Optional[str] = None
    linked_entity_id: Optional[int] = None


class BIMAnnotationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    project_id: int
    model_id: Optional[int] = None
    world_pos_x: float = 0
    world_pos_y: float = 0
    world_pos_z: float = 0
    eye_x: Optional[float] = None
    eye_y: Optional[float] = None
    eye_z: Optional[float] = None
    look_x: Optional[float] = None
    look_y: Optional[float] = None
    look_z: Optional[float] = None
    up_x: Optional[float] = None
    up_y: Optional[float] = None
    up_z: Optional[float] = None
    entity_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    status: str = "open"
    assigned_to: Optional[int] = None
    linked_entity_type: Optional[str] = None
    linked_entity_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
