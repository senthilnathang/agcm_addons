"""API routes for Bid Packages and Submissions"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

from addons.agcm_portal.schemas.bid import (
    BidPackageCreate, BidPackageUpdate, BidPackageResponse,
    BidSubmissionCreate, BidSubmissionUpdate, BidSubmissionResponse,
)
from addons.agcm_portal.services.portal_service import PortalService

router = APIRouter()


def _get_service(db: Session, current_user) -> PortalService:
    company_id = get_effective_company_id(current_user, db)
    return PortalService(db=db, company_id=company_id, user_id=current_user.id)


@router.get("/bid-packages", response_model=None)
async def list_bid_packages(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """List bid packages with pagination."""
    svc = _get_service(db, current_user)
    return svc.list_bid_packages(
        page=page, page_size=page_size,
        project_id=project_id, status=status, search=search,
    )


@router.get("/bid-packages/{bid_package_id}", response_model=None)
async def get_bid_package(
    bid_package_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get bid package with submissions."""
    svc = _get_service(db, current_user)
    bp = svc.get_bid_package(bid_package_id)
    if not bp:
        raise HTTPException(status_code=404, detail="Bid package not found")
    return BidPackageResponse.model_validate(bp).model_dump()


@router.post("/bid-packages", response_model=None, status_code=201)
async def create_bid_package(
    data: BidPackageCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new bid package."""
    svc = _get_service(db, current_user)
    bp = svc.create_bid_package(data)
    return BidPackageResponse.model_validate(bp).model_dump()


@router.put("/bid-packages/{bid_package_id}", response_model=None)
async def update_bid_package(
    bid_package_id: int,
    data: BidPackageUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a bid package."""
    svc = _get_service(db, current_user)
    bp = svc.update_bid_package(bid_package_id, data)
    if not bp:
        raise HTTPException(status_code=404, detail="Bid package not found")
    return BidPackageResponse.model_validate(bp).model_dump()


@router.delete("/bid-packages/{bid_package_id}", status_code=204)
async def delete_bid_package(
    bid_package_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a bid package."""
    svc = _get_service(db, current_user)
    if not svc.delete_bid_package(bid_package_id):
        raise HTTPException(status_code=404, detail="Bid package not found")


# --- Submissions ---

@router.post("/bid-packages/{bid_package_id}/submissions", response_model=None, status_code=201)
async def create_submission(
    bid_package_id: int,
    data: BidSubmissionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add a submission to a bid package."""
    svc = _get_service(db, current_user)
    sub = svc.create_submission(bid_package_id, data)
    if not sub:
        raise HTTPException(status_code=404, detail="Bid package not found")
    return BidSubmissionResponse.model_validate(sub).model_dump()


@router.put("/submissions/{submission_id}", response_model=None)
async def update_submission(
    submission_id: int,
    data: BidSubmissionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a bid submission."""
    svc = _get_service(db, current_user)
    sub = svc.update_submission(submission_id, data)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    return BidSubmissionResponse.model_validate(sub).model_dump()


@router.delete("/submissions/{submission_id}", status_code=204)
async def delete_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a bid submission."""
    svc = _get_service(db, current_user)
    if not svc.delete_submission(submission_id):
        raise HTTPException(status_code=404, detail="Submission not found")


@router.post("/submissions/{submission_id}/award", response_model=None)
async def award_bid(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Award a bid to a submission, rejecting all others in the package."""
    svc = _get_service(db, current_user)
    sub = svc.award_bid(submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    return BidSubmissionResponse.model_validate(sub).model_dump()
