"""AG CM Safety API Routes"""

from fastapi import APIRouter

from addons.agcm_safety.api.checklists import router as checklists_router
from addons.agcm_safety.api.inspections import router as inspections_router
from addons.agcm_safety.api.punch_list import router as punch_list_router
from addons.agcm_safety.api.incidents import router as incidents_router

router = APIRouter()
router.include_router(checklists_router)
router.include_router(inspections_router)
router.include_router(punch_list_router)
router.include_router(incidents_router)
