"""AG CM BIM API Routes"""

from fastapi import APIRouter

from addons.agcm_bim.api.bim_models import router as models_router
from addons.agcm_bim.api.viewpoints import router as viewpoints_router
from addons.agcm_bim.api.clash import router as clash_router

router = APIRouter()
router.include_router(models_router)
router.include_router(viewpoints_router)
router.include_router(clash_router)
