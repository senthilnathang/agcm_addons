"""AG CM API Routes"""

from fastapi import APIRouter

from addons.agcm.api.projects import router as projects_router
from addons.agcm.api.daily_logs import router as daily_logs_router
from addons.agcm.api.settings import router as settings_router
from addons.agcm.api.weather import router as weather_router
from addons.agcm.api.photos import router as photos_router
from addons.agcm.api.dashboard import router as dashboard_router
from addons.agcm.api.comments import router as comments_router

router = APIRouter()
router.include_router(projects_router)
router.include_router(daily_logs_router)
router.include_router(settings_router)
router.include_router(weather_router)
router.include_router(photos_router)
router.include_router(dashboard_router)
router.include_router(comments_router)
