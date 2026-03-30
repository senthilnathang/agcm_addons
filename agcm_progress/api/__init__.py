"""AGCM Progress API Routes"""

from fastapi import APIRouter

from addons.agcm_progress.api.milestones import router as milestones_router
from addons.agcm_progress.api.issues import router as issues_router
from addons.agcm_progress.api.estimation import router as estimation_router
from addons.agcm_progress.api.scurve import router as scurve_router
from addons.agcm_progress.api.project_images import router as project_images_router

router = APIRouter()
router.include_router(milestones_router)
router.include_router(issues_router)
router.include_router(estimation_router)
router.include_router(scurve_router)
router.include_router(project_images_router)
