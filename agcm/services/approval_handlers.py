"""
AGCM Approval Completion Handlers — dispatches entity-specific actions when
an approval chain completes (approved or rejected).

Called from the AGCM approval API endpoints after ApprovalService.approve_task()
or reject_task() signals chain_complete=True.
"""

import logging
import sys
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _get_post_to_budget():
    """Get the post_to_budget function, handling both runtime and test environments."""
    mod = sys.modules.get("agcm_budget_posting")
    if mod:
        return mod.post_to_budget
    try:
        import importlib
        mod = importlib.import_module("addons.agcm.services.budget_posting")
        return mod.post_to_budget
    except ImportError:
        # Direct file import fallback
        import importlib.util
        import os
        path = os.path.join(os.path.dirname(__file__), "budget_posting.py")
        spec = importlib.util.spec_from_file_location("agcm_budget_posting", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["agcm_budget_posting"] = mod
        spec.loader.exec_module(mod)
        return mod.post_to_budget


def _import_model(addon_module: str, file_name: str, *class_names: str):
    """Import model classes, handling both runtime (addons.*) and test environments."""
    # Check if already loaded by test conftest (importlib pre-loading)
    cache_key = f"{addon_module}_{file_name}"
    mod = sys.modules.get(cache_key)
    if not mod:
        # Runtime import via addons namespace
        import importlib
        mod = importlib.import_module(f"addons.{addon_module}.models.{file_name}")
    if len(class_names) == 1:
        return getattr(mod, class_names[0])
    return tuple(getattr(mod, cn) for cn in class_names)


# ---------------------------------------------------------------------------
# Handler functions — one per entity type
# ---------------------------------------------------------------------------

def _handle_po_approval(db: Session, entity_id: int, user_id: int, outcome: str):
    post_to_budget = _get_post_to_budget()

    PurchaseOrder, PurchaseOrderStatus = _import_model(
        "agcm_procurement", "purchase_order", "PurchaseOrder", "PurchaseOrderStatus")
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == entity_id).first()
    if not po:
        return
    if outcome == "APPROVED":
        po.status = PurchaseOrderStatus.APPROVED.value
        po.approved_by = user_id
        po.approved_date = date.today()
        # Post committed cost to budget
        if po.project_id and po.total_amount:
            post_to_budget(db, po.project_id, po.company_id,
                           "committed_amount", po.total_amount,
                           description="Purchase Orders")
    else:
        po.status = PurchaseOrderStatus.REJECTED.value
    po.updated_by = user_id


def _handle_subcontract_approval(db: Session, entity_id: int, user_id: int, outcome: str):
    post_to_budget = _get_post_to_budget()

    Subcontract, SubcontractStatus = _import_model(
        "agcm_procurement", "subcontract", "Subcontract", "SubcontractStatus")
    sc = db.query(Subcontract).filter(Subcontract.id == entity_id).first()
    if not sc:
        return
    if outcome == "APPROVED":
        sc.status = SubcontractStatus.APPROVED.value
        sc.approved_by = user_id
        sc.approved_date = date.today()
        # Post committed cost to budget
        amount = getattr(sc, "revised_amount", None) or getattr(sc, "original_amount", 0)
        if sc.project_id and amount:
            post_to_budget(db, sc.project_id, sc.company_id,
                           "committed_amount", amount,
                           description="Subcontracts")
    else:
        sc.status = SubcontractStatus.CANCELLED.value
    sc.updated_by = user_id


def _handle_vendor_bill_approval(db: Session, entity_id: int, user_id: int, outcome: str):
    post_to_budget = _get_post_to_budget()

    VendorBill, VendorBillStatus = _import_model(
        "agcm_procurement", "vendor_bill", "VendorBill", "VendorBillStatus")
    bill = db.query(VendorBill).filter(VendorBill.id == entity_id).first()
    if not bill:
        return
    if outcome == "APPROVED":
        bill.status = VendorBillStatus.APPROVED.value
        bill.approved_by = user_id
        bill.approved_date = date.today()
        # Post actual cost to budget
        if bill.project_id and bill.total_amount:
            post_to_budget(db, bill.project_id, bill.company_id,
                           "actual_amount", bill.total_amount,
                           description="Vendor Bills")
    else:
        bill.status = VendorBillStatus.VOID.value
    bill.updated_by = user_id


def _handle_change_order_approval(db: Session, entity_id: int, user_id: int, outcome: str):
    post_to_budget = _get_post_to_budget()

    ChangeOrder, ChangeOrderStatus = _import_model(
        "agcm_change_order", "change_order", "ChangeOrder", "ChangeOrderStatus")
    co = db.query(ChangeOrder).filter(ChangeOrder.id == entity_id).first()
    if not co:
        return

    if outcome == "APPROVED":
        co.status = ChangeOrderStatus.APPROVED.value
        co.approved_by = user_id
        co.approved_date = date.today()
        # Post committed cost to budget
        if co.project_id and co.cost_impact:
            post_to_budget(db, co.project_id, co.company_id,
                           "committed_amount", co.cost_impact,
                           description="Approved Change Orders")
    else:
        co.status = ChangeOrderStatus.REJECTED.value

    co.updated_by = user_id


def _handle_estimate_approval(db: Session, entity_id: int, user_id: int, outcome: str):
    Estimate, EstimateStatus = _import_model(
        "agcm_estimate", "estimate", "Estimate", "EstimateStatus")
    estimate = db.query(Estimate).filter(Estimate.id == entity_id).first()
    if not estimate:
        return
    if outcome == "APPROVED":
        estimate.status = EstimateStatus.APPROVED.value
        estimate.approved_by = user_id
        estimate.approved_date = date.today()
    else:
        estimate.status = EstimateStatus.REJECTED.value
    estimate.updated_by = user_id


def _handle_proposal_approval(db: Session, entity_id: int, user_id: int, outcome: str):
    Proposal, ProposalStatus = _import_model(
        "agcm_estimate", "proposal", "Proposal", "ProposalStatus")
    proposal = db.query(Proposal).filter(Proposal.id == entity_id).first()
    if not proposal:
        return
    if outcome == "APPROVED":
        proposal.status = ProposalStatus.APPROVED.value
        proposal.approved_by = user_id
        proposal.approved_date = date.today()
    else:
        proposal.status = ProposalStatus.REJECTED.value
    proposal.updated_by = user_id


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

APPROVAL_HANDLERS = {
    "purchase_order": _handle_po_approval,
    "subcontract": _handle_subcontract_approval,
    "vendor_bill": _handle_vendor_bill_approval,
    "change_order": _handle_change_order_approval,
    "estimate": _handle_estimate_approval,
    "proposal": _handle_proposal_approval,
}


def on_approval_complete(
    db: Session,
    entity_type: str,
    entity_id: int,
    user_id: int,
    outcome: str,
) -> bool:
    """
    Dispatch to the appropriate handler when an approval chain completes.

    Args:
        db: Database session
        entity_type: e.g. "purchase_order"
        entity_id: The entity record ID
        user_id: The user who made the final decision
        outcome: "APPROVED" or "REJECTED"

    Returns:
        True if handler was found and executed, False otherwise.
    """
    handler = APPROVAL_HANDLERS.get(entity_type)
    if not handler:
        logger.warning("No approval handler for entity_type=%s", entity_type)
        return False

    try:
        handler(db, entity_id, user_id, outcome)
        logger.info(
            "Approval %s for %s #%d — handler executed",
            outcome, entity_type, entity_id,
        )
        return True
    except Exception as e:
        logger.error(
            "Approval handler failed for %s #%d: %s",
            entity_type, entity_id, e,
        )
        return False
