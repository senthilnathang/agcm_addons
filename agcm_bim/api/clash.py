"""API routes for Clash Detection"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_bim.schemas.bim import (
    ClashTestCreate, ClashTestUpdate, ClashTestResponse, ClashTestDetail,
    ClashResultUpdate, ClashResultResponse, ClashResultResolve, ClashResultAssign,
)
from addons.agcm_bim.services.bim_service import BIMService

router = APIRouter()


def _get_service(db: Session, current_user) -> BIMService:
    company_id = get_effective_company_id(current_user, db)
    return BIMService(db, company_id, current_user.id)


# ─── Clash Tests ─────────────────────────────────────────────────────────────

@router.get("/clash-tests")
async def list_clash_tests(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.list_clash_tests(project_id, status, page, page_size)
    result["items"] = [ClashTestResponse.model_validate(i).model_dump() for i in result["items"]]
    return result


@router.get("/clash-tests/{test_id}", response_model=ClashTestDetail)
async def get_clash_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    detail = svc.get_clash_test_detail(test_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Clash test not found")
    return detail


@router.post("/clash-tests", response_model=ClashTestResponse, status_code=201)
async def create_clash_test(
    data: ClashTestCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    return svc.create_clash_test(data)


@router.put("/clash-tests/{test_id}", response_model=ClashTestResponse)
async def update_clash_test(
    test_id: int,
    data: ClashTestUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.update_clash_test(test_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Clash test not found")
    return result


@router.delete("/clash-tests/{test_id}", status_code=204)
async def delete_clash_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    if not svc.delete_clash_test(test_id):
        raise HTTPException(status_code=404, detail="Clash test not found")


@router.post("/clash-tests/{test_id}/run", response_model=ClashTestResponse)
async def run_clash_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Execute clash detection between the configured models."""
    svc = _get_service(db, current_user)
    result = svc.run_clash_test(test_id)
    if not result:
        raise HTTPException(status_code=404, detail="Clash test not found")
    return result


# ─── Clash Results ───────────────────────────────────────────────────────────

@router.get("/clash-tests/{test_id}/results")
async def list_clash_results(
    test_id: int,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    page: int = 1,
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.list_clash_results(test_id, status, severity, page, page_size)
    result["items"] = [ClashResultResponse.model_validate(i).model_dump() for i in result["items"]]
    return result


@router.get("/clash-results/{result_id}", response_model=ClashResultResponse)
async def get_clash_result(
    result_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.get_clash_result(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Clash result not found")
    return result


@router.put("/clash-results/{result_id}", response_model=ClashResultResponse)
async def update_clash_result(
    result_id: int,
    data: ClashResultUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.update_clash_result(result_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Clash result not found")
    return result


@router.post("/clash-results/{result_id}/resolve", response_model=ClashResultResponse)
async def resolve_clash(
    result_id: int,
    data: ClashResultResolve,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.resolve_clash(result_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Clash result not found")
    return result


@router.post("/clash-results/{result_id}/assign", response_model=ClashResultResponse)
async def assign_clash(
    result_id: int,
    data: ClashResultAssign,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.assign_clash(result_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Clash result not found")
    return result


@router.post("/clash-results/{result_id}/ignore", response_model=ClashResultResponse)
async def ignore_clash(
    result_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    svc = _get_service(db, current_user)
    result = svc.ignore_clash(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Clash result not found")
    return result
