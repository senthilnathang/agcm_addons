"""AGCM Schedule API Routes"""

from fastapi import APIRouter

from addons.agcm_schedule.api.schedules import router as schedules_router
from addons.agcm_schedule.api.tasks import router as tasks_router
from addons.agcm_schedule.api.gantt import router as gantt_router

router = APIRouter()
router.include_router(schedules_router)
router.include_router(tasks_router)
router.include_router(gantt_router)
