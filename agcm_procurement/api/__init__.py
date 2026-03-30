"""AGCM Procurement API Routes"""

from fastapi import APIRouter

from addons.agcm_procurement.api.purchase_orders import router as po_router
from addons.agcm_procurement.api.subcontracts import router as sc_router
from addons.agcm_procurement.api.vendor_bills import router as vb_router

router = APIRouter()
router.include_router(po_router)
router.include_router(sc_router)
router.include_router(vb_router)
