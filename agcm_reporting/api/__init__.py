"""AGCM Reporting API Routes"""

from fastapi import APIRouter

from addons.agcm_reporting.api.reports import router as reports_router
from addons.agcm_reporting.api.dashboards import router as dashboards_router

router = APIRouter()
router.include_router(reports_router)
router.include_router(dashboards_router)
