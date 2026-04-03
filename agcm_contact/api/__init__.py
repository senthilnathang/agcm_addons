"""AG CM Contact API Routes"""

from fastapi import APIRouter

from addons.agcm_contact.api.vendors import router as vendors_router

router = APIRouter()
router.include_router(vendors_router)
