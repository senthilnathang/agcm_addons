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
    PurchaseOrder, PurchaseOrderStatus = _import_model(
        "agcm_procurement", "purchase_order", "PurchaseOrder", "PurchaseOrderStatus")
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == entity_id).first()
    if not po:
        return
    if outcome == "APPROVED":
        po.status = PurchaseOrderStatus.APPROVED.value
        po.approved_by = user_id
        po.approved_date = date.today()
    else:
        po.status = PurchaseOrderStatus.REJECTED.value
    po.updated_by = user_id


def _handle_subcontract_approval(db: Session, entity_id: int, user_id: int, outcome: str):
    Subcontract, SubcontractStatus = _import_model(
        "agcm_procurement", "subcontract", "Subcontract", "SubcontractStatus")
    sc = db.query(Subcontract).filter(Subcontract.id == entity_id).first()
    if not sc:
        return
    if outcome == "APPROVED":
        sc.status = SubcontractStatus.APPROVED.value
        sc.approved_by = user_id
        sc.approved_date = date.today()
    else:
        sc.status = SubcontractStatus.CANCELLED.value
    sc.updated_by = user_id


def _handle_vendor_bill_approval(db: Session, entity_id: int, user_id: int, outcome: str):
    VendorBill, VendorBillStatus = _import_model(
        "agcm_procurement", "vendor_bill", "VendorBill", "VendorBillStatus")
    bill = db.query(VendorBill).filter(VendorBill.id == entity_id).first()
    if not bill:
        return
    if outcome == "APPROVED":
        bill.status = VendorBillStatus.APPROVED.value
        bill.approved_by = user_id
        bill.approved_date = date.today()
    else:
        bill.status = VendorBillStatus.VOID.value
    bill.updated_by = user_id


def _handle_change_order_approval(db: Session, entity_id: int, user_id: int, outcome: str):
    ChangeOrder, ChangeOrderStatus = _import_model(
        "agcm_change_order", "change_order", "ChangeOrder", "ChangeOrderStatus")
    co = db.query(ChangeOrder).filter(ChangeOrder.id == entity_id).first()
    if not co:
        return

    if outcome == "APPROVED":
        co.status = ChangeOrderStatus.APPROVED.value
        co.approved_by = user_id
        co.approved_date = date.today()

        # Side effect: update budget committed_amount (same logic as original)
        try:
            Budget = _import_model("agcm_finance", "budget", "Budget")
            if co.project_id and co.cost_impact:
                budget_line = (
                    db.query(Budget)
                    .filter(
                        Budget.project_id == co.project_id,
                        Budget.company_id == co.company_id,
                        Budget.description.ilike("%Approved Change Orders%"),
                    )
                    .first()
                )
                if budget_line:
                    budget_line.committed_amount = (
                        budget_line.committed_amount or 0
                    ) + co.cost_impact
                else:
                    budget_line = Budget(
                        project_id=co.project_id,
                        cost_code_id=None,
                        description="Approved Change Orders",
                        planned_amount=0,
                        actual_amount=0,
                        committed_amount=co.cost_impact,
                        company_id=co.company_id,
                    )
                    db.add(budget_line)
        except ImportError:
            logger.debug("agcm_finance not installed — skipping budget update")
        except Exception as e:
            logger.warning("Failed to update budget for CO #%d: %s", entity_id, e)
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
