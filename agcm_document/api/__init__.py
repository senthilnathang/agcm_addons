"""AG CM Document API Routes"""

from fastapi import APIRouter

from addons.agcm_document.api.documents import router as documents_router

router = APIRouter()
router.include_router(documents_router)
