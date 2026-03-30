"""AGCM Estimate API Routes"""

from fastapi import APIRouter

from addons.agcm_estimate.api.catalogs import router as catalogs_router
from addons.agcm_estimate.api.assemblies import router as assemblies_router
from addons.agcm_estimate.api.estimates import router as estimates_router
from addons.agcm_estimate.api.proposals import router as proposals_router
from addons.agcm_estimate.api.takeoffs import router as takeoffs_router

router = APIRouter()
router.include_router(catalogs_router)
router.include_router(assemblies_router)
router.include_router(estimates_router)
router.include_router(proposals_router)
router.include_router(takeoffs_router)
