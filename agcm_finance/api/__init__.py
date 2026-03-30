"""AG CM Finance API Routes"""

from fastapi import APIRouter

from addons.agcm_finance.api.cost_codes import router as cost_codes_router
from addons.agcm_finance.api.budgets import router as budgets_router
from addons.agcm_finance.api.expenses import router as expenses_router
from addons.agcm_finance.api.invoices import router as invoices_router
from addons.agcm_finance.api.bills import router as bills_router

router = APIRouter()
router.include_router(cost_codes_router)
router.include_router(budgets_router)
router.include_router(expenses_router)
router.include_router(invoices_router)
router.include_router(bills_router)
