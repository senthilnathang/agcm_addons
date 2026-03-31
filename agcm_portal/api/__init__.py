"""AGCM Portal API Routes"""

from fastapi import APIRouter

from addons.agcm_portal.api.selections import router as selections_router
from addons.agcm_portal.api.bids import router as bids_router
from addons.agcm_portal.api.portal_config import router as portal_config_router

router = APIRouter()
router.include_router(selections_router)
router.include_router(bids_router)
router.include_router(portal_config_router)
