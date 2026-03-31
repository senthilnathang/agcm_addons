"""API routes for BIM Models — includes XKT streaming and IFC→XKT conversion"""

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse, Response
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


# ═══════════════════════════════════════════════════════════════════
# XKT Streaming — serve converted .xkt files to xeokit viewer
# ═══════════════════════════════════════════════════════════════════

@router.get("/models/{model_id}/xkt")
async def serve_xkt_file(
    model_id: int,
    token: Optional[str] = Query(None, description="JWT token for xeokit direct fetch"),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """
    Stream the converted .xkt file for the xeokit viewer.
    Supports both Authorization header and ?token= query param
    (xeokit XKTLoaderPlugin.load() makes raw fetch without auth headers).
    """
    # Resolve user from header or token query param (same pattern as reports)
    from app.auth.deps import get_current_user as _get_user
    try:
        if token:
            from app.core.security import decode_access_token
            payload = decode_access_token(token)
            from app.models import User
            current_user = db.query(User).filter(User.id == payload.get("sub")).first()
            if not current_user:
                raise HTTPException(status_code=401, detail="Invalid token")
        else:
            current_user = await _get_user(request=request, db=db)
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication required. Pass ?token=JWT for xeokit viewer.")

    svc = _get_service(db, current_user)
    model = svc.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="BIM model not found")

    # Derive XKT path from original file path
    xkt_url = getattr(model, 'xkt_file_url', None)
    if not xkt_url and model.file_url:
        # Convention: same path but .xkt extension
        base, _ = os.path.splitext(model.file_url)
        xkt_url = f"{base}.xkt"

    if not xkt_url:
        raise HTTPException(status_code=404, detail="XKT file not available. Run conversion first.")

    # Try to serve from storage
    try:
        from app.services.storage import storage_service
        content = await storage_service.get_file_content(xkt_url.lstrip('/'))
        if content:
            return Response(
                content=content,
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f"inline; filename={model_id}.xkt",
                    "Cache-Control": "public, max-age=86400",
                },
            )
    except Exception:
        pass

    # Fallback: serve from filesystem
    local_path = xkt_url.lstrip('/')
    if os.path.exists(local_path):
        return FileResponse(
            local_path,
            media_type="application/octet-stream",
            headers={"Cache-Control": "public, max-age=86400"},
        )

    raise HTTPException(status_code=404, detail="XKT file not found on disk")


@router.get("/models/{model_id}/metadata")
async def serve_model_metadata(
    model_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Serve IFC metadata JSON for the xeokit MetaModel."""
    svc = _get_service(db, current_user)
    model = svc.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="BIM model not found")

    import json
    metadata = model.metadata_json
    if metadata:
        try:
            return json.loads(metadata) if isinstance(metadata, str) else metadata
        except Exception:
            pass

    # Build metadata from extracted elements
    summary = svc.get_model_summary(model_id)
    return summary or {}


# ═══════════════════════════════════════════════════════════════════
# IFC → XKT Conversion — trigger via job queue
# ═══════════════════════════════════════════════════════════════════

@router.post("/models/{model_id}/convert")
async def convert_to_xkt(
    model_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Trigger IFC → XKT conversion via the background job queue.
    Requires convert2xkt (from @xeokit/xeokit-convert) to be installed.
    """
    svc = _get_service(db, current_user)
    model = svc.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="BIM model not found")

    if not model.file_url:
        raise HTTPException(status_code=400, detail="No source file uploaded")

    if model.file_format not in ("ifc",):
        raise HTTPException(status_code=400, detail=f"Conversion not supported for .{model.file_format} (only IFC)")

    # Queue the conversion job
    try:
        from app.core.job_queue import job_queue
        job_id = job_queue.enqueue(
            _convert_ifc_to_xkt_job,
            model_id=model.id,
            source_path=model.file_url.lstrip('/'),
            company_id=svc.company_id,
            queue="low",
            max_retries=2,
            timeout=600,
        )

        # Update status
        model.status = "processing"
        db.commit()

        return {"model_id": model.id, "status": "processing", "job_id": job_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue conversion: {e}")


def _convert_ifc_to_xkt_job(model_id: int, source_path: str, company_id: int):
    """
    Background job: Convert IFC → XKT using convert2xkt CLI.
    Called by the Redis job queue worker.
    """
    import subprocess
    import tempfile
    import logging

    logger = logging.getLogger(__name__)

    try:
        from app.core.config import settings
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
        db = sessionmaker(bind=engine)()

        # Load the model
        from addons.agcm_bim.models.bim_model import BIMModel
        model = db.query(BIMModel).filter(BIMModel.id == model_id).first()
        if not model:
            logger.error(f"BIM model {model_id} not found")
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            local_ifc = os.path.join(tmpdir, "model.ifc")
            local_xkt = os.path.join(tmpdir, "model.xkt")

            # Download source file
            if os.path.exists(source_path):
                import shutil
                shutil.copy(source_path, local_ifc)
            else:
                logger.error(f"Source IFC file not found: {source_path}")
                model.status = "failed"
                model.processing_error = f"Source file not found: {source_path}"
                db.commit()
                db.close()
                return

            # Run convert2xkt
            result = subprocess.run(
                ["convert2xkt", "-s", local_ifc, "-o", local_xkt],
                capture_output=True, text=True, timeout=600,
            )

            if result.returncode != 0:
                model.status = "failed"
                model.processing_error = f"convert2xkt failed: {result.stderr[:500]}"
                db.commit()
                db.close()
                return

            # Store XKT file
            xkt_dir = os.path.dirname(source_path)
            xkt_path = os.path.join(xkt_dir, f"model_{model_id}.xkt")
            os.makedirs(os.path.dirname(xkt_path), exist_ok=True)

            import shutil
            shutil.copy(local_xkt, xkt_path)

            # Update model
            model.status = "ready"
            model.xkt_file_url = f"/{xkt_path}" if not xkt_path.startswith('/') else xkt_path
            model.processing_error = None
            db.commit()

            logger.info(f"BIM model {model_id} converted to XKT: {xkt_path}")

        db.close()

    except subprocess.TimeoutExpired:
        logger.error(f"convert2xkt timed out for model {model_id}")
    except FileNotFoundError:
        logger.error("convert2xkt not installed. Run: npm install -g @xeokit/xeokit-convert")
    except Exception as e:
        logger.error(f"IFC→XKT conversion failed for model {model_id}: {e}")
