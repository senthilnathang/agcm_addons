"""AG CM Resource API Routes"""

from fastapi import APIRouter

from addons.agcm_resource.api.workers import router as workers_router
from addons.agcm_resource.api.equipment import router as equipment_router
from addons.agcm_resource.api.timesheets import router as timesheets_router

router = APIRouter()
router.include_router(workers_router)
router.include_router(equipment_router)
router.include_router(timesheets_router)
