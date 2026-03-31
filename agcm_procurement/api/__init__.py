"""AGCM Procurement API Routes"""

from fastapi import APIRouter

from addons.agcm_procurement.api.purchase_orders import router as po_router
from addons.agcm_procurement.api.subcontracts import router as sc_router
from addons.agcm_procurement.api.vendor_bills import router as vb_router
from addons.agcm_procurement.api.payment_applications import router as pa_router
from addons.agcm_procurement.api.tm_tickets import router as tm_router

router = APIRouter()
router.include_router(po_router)
router.include_router(sc_router)
router.include_router(vb_router)
router.include_router(pa_router)
router.include_router(tm_router)
