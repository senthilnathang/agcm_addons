"""API routes for BIM Models"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_bim.schemas.bim import (
    BIMModelCreate, BIMModelUpdate, BIMModelResponse, BIMModelDetail,
    BIMModelSummary, BIMElementResponse,
)
from addons.agcm_bim.services.bim_service import BIMService

router = APIRouter()


def _get_service(db: Session, current_user) -> BIMService:
    company_id = get_effective_company_id(current_user, db)
    return BIMService(db, company_id, current_user.id)


@router.get("/models")
async def list_models(
    project_id: Optional[int] = None,
    discipline: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_only: bool = True,
    page: int = 1,
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.list_models(project_id, discipline, status, search, current_only, page, page_size)
    result["items"] = [BIMModelResponse.model_validate(i).model_dump() for i in result["items"]]
    return result


@router.get("/models/{model_id}", response_model=BIMModelDetail)
async def get_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    detail = svc.get_model_detail(model_id)
    if not detail:
        raise HTTPException(status_code=404, detail="BIM model not found")
    return detail


@router.post("/models", response_model=BIMModelResponse, status_code=201)
async def create_model(
    data: BIMModelCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    return svc.create_model(data)


@router.put("/models/{model_id}", response_model=BIMModelResponse)
async def update_model(
    model_id: int,
    data: BIMModelUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.update_model(model_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="BIM model not found")
    return result


@router.delete("/models/{model_id}", status_code=204)
async def delete_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    if not svc.delete_model(model_id):
        raise HTTPException(status_code=404, detail="BIM model not found")


@router.post("/models/{model_id}/upload", response_model=BIMModelResponse)
async def upload_model_file(
    model_id: int,
    file_url: str = Query(...),
    file_name: str = Query(...),
    file_size: int = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update model with file info after upload (file stored via documents module)."""
    svc = _get_service(db, current_user)
    result = svc.update_model_file(model_id, file_url, file_name, file_size)
    if not result:
        raise HTTPException(status_code=404, detail="BIM model not found")
    return result


@router.post("/models/{model_id}/process", response_model=BIMModelResponse)
async def process_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Trigger model processing (metadata extraction, element counting)."""
    svc = _get_service(db, current_user)
    result = svc.process_model(model_id)
    if not result:
        raise HTTPException(status_code=404, detail="BIM model not found")
    return result


@router.post("/models/{model_id}/new-version", response_model=BIMModelResponse, status_code=201)
async def create_model_version(
    model_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new version of an existing model."""
    svc = _get_service(db, current_user)
    result = svc.create_model_version(model_id)
    if not result:
        raise HTTPException(status_code=404, detail="BIM model not found")
    return result


@router.get("/models/{model_id}/versions")
async def get_model_versions(
    model_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    versions = svc.get_model_versions(model_id)
    return [BIMModelResponse.model_validate(v).model_dump() for v in versions]


@router.get("/models/{model_id}/summary", response_model=BIMModelSummary)
async def get_model_summary(
    model_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get element counts grouped by type, level, material, discipline."""
    svc = _get_service(db, current_user)
    summary = svc.get_model_summary(model_id)
    if not summary:
        raise HTTPException(status_code=404, detail="BIM model not found")
    return summary


@router.get("/models/{model_id}/elements")
async def search_elements(
    model_id: int,
    ifc_type: Optional[str] = None,
    name: Optional[str] = None,
    level: Optional[str] = None,
    material: Optional[str] = None,
    page: int = 1,
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.search_elements(model_id, ifc_type, name, level, material, page, page_size)
    result["items"] = [BIMElementResponse.model_validate(i).model_dump() for i in result["items"]]
    return result
