"""AG CM RFI API Routes"""

from fastapi import APIRouter

from addons.agcm_rfi.api.rfis import router as rfis_router
from addons.agcm_rfi.api.labels import router as labels_router

router = APIRouter()
router.include_router(rfis_router)
router.include_router(labels_router)
