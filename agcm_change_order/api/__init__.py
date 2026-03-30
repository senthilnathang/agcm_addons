"""AG CM Change Order API Routes"""

from fastapi import APIRouter

from addons.agcm_change_order.api.change_orders import router as change_orders_router

router = APIRouter()
router.include_router(change_orders_router)
