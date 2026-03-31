"""AG CM Document API Routes"""

from fastapi import APIRouter

from addons.agcm_document.api.documents import router as documents_router
from addons.agcm_document.api.drawings import router as drawings_router

router = APIRouter()
router.include_router(documents_router)
router.include_router(drawings_router)
