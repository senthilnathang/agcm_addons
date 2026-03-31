"""API routes for Equipment and Equipment Assignments"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_resource.schemas.resource import (
    EquipmentCreate, EquipmentUpdate, EquipmentResponse,
    EquipmentAssignmentCreate, EquipmentAssignmentUpdate,
)
from addons.agcm_resource.services.resource_service import ResourceService

router = APIRouter()


def _get_service(db: Session, current_user) -> ResourceService:
    company_id = get_effective_company_id(current_user, db)
    return ResourceService(db=db, company_id=company_id, user_id=current_user.id)


# =========================================================================
# EQUIPMENT CRUD
# =========================================================================

@router.get("/equipment", response_model=None)
async def list_equipment(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status: Optional[str] = Query(None, description="Filter by status"),
    equipment_type: Optional[str] = Query(None, description="Filter by equipment type"),
    project_id: Optional[int] = Query(None, description="Filter by current project"),
    search: Optional[str] = Query(None, description="Search by name, sequence, type, make, serial"),
):
    """List equipment with pagination and filtering."""
    svc = _get_service(db, current_user)
    return svc.list_equipment(
        page=page, page_size=page_size, status=status,
        equipment_type=equipment_type, project_id=project_id, search=search,
    )


@router.get("/equipment/{equipment_id}", response_model=None)
async def get_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get equipment details."""
    svc = _get_service(db, current_user)
    equipment = svc.get_equipment(equipment_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return EquipmentResponse.model_validate(equipment).model_dump()


@router.post("/equipment", response_model=None, status_code=201)
async def create_equipment(
    data: EquipmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create new equipment."""
    svc = _get_service(db, current_user)
    equipment = svc.create_equipment(data)
    return EquipmentResponse.model_validate(equipment).model_dump()


@router.put("/equipment/{equipment_id}", response_model=None)
async def update_equipment(
    equipment_id: int,
    data: EquipmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update equipment."""
    svc = _get_service(db, current_user)
    equipment = svc.update_equipment(equipment_id, data)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return EquipmentResponse.model_validate(equipment).model_dump()


@router.delete("/equipment/{equipment_id}", status_code=204)
async def delete_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete equipment."""
    svc = _get_service(db, current_user)
    if not svc.delete_equipment(equipment_id):
        raise HTTPException(status_code=404, detail="Equipment not found")


@router.get("/equipment/{equipment_id}/utilization", response_model=None)
async def equipment_utilization(
    equipment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get utilization stats for a piece of equipment."""
    svc = _get_service(db, current_user)
    result = svc.calculate_utilization(equipment_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# =========================================================================
# EQUIPMENT ASSIGNMENTS
# =========================================================================

@router.get("/equipment-assignments", response_model=None)
async def list_equipment_assignments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    equipment_id: Optional[int] = Query(None, description="Filter by equipment"),
    project_id: Optional[int] = Query(None, description="Filter by project"),
):
    """List equipment assignments."""
    svc = _get_service(db, current_user)
    return svc.list_equipment_assignments(
        page=page, page_size=page_size, equipment_id=equipment_id, project_id=project_id,
    )


@router.get("/equipment-assignments/{assignment_id}", response_model=None)
async def get_equipment_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get equipment assignment details."""
    svc = _get_service(db, current_user)
    assignment = svc.get_equipment_assignment(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@router.post("/equipment-assignments", response_model=None, status_code=201)
async def create_equipment_assignment(
    data: EquipmentAssignmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create equipment assignment."""
    svc = _get_service(db, current_user)
    assignment = svc.create_equipment_assignment(data)
    return assignment


@router.put("/equipment-assignments/{assignment_id}", response_model=None)
async def update_equipment_assignment(
    assignment_id: int,
    data: EquipmentAssignmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update equipment assignment."""
    svc = _get_service(db, current_user)
    assignment = svc.update_equipment_assignment(assignment_id, data)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@router.delete("/equipment-assignments/{assignment_id}", status_code=204)
async def delete_equipment_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete equipment assignment."""
    svc = _get_service(db, current_user)
    if not svc.delete_equipment_assignment(assignment_id):
        raise HTTPException(status_code=404, detail="Assignment not found")
