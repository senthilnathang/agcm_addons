"""
Tests for AGCM approval chain integration.

Verifies:
- Backward compatibility: auto-approve when no chain configured
- Chain flow: entity → pending_approval → approved on chain completion
- Rejection: entity → pending_approval → rejected on chain rejection
- CO budget side effect preserved on chain approval
- Handler registry completeness
"""

import importlib.util
import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import text

# Set up 'addons' namespace so handler imports like
# 'from addons.agcm_procurement.models...' resolve in tests
ADDONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.abspath(os.path.join(ADDONS_DIR, "..", "backend"))

# Create a fake 'addons' package pointing to agcm_addons directory
import types
if "addons" not in sys.modules:
    addons_pkg = types.ModuleType("addons")
    addons_pkg.__path__ = [ADDONS_DIR]
    addons_pkg.__package__ = "addons"
    sys.modules["addons"] = addons_pkg

def _load_service(file_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

_handlers_mod = _load_service(
    os.path.join(ADDONS_DIR, "agcm", "services", "approval_handlers.py"),
    "agcm_approval_handlers",
)
_integration_mod = _load_service(
    os.path.join(ADDONS_DIR, "agcm", "services", "approval_integration.py"),
    "agcm_approval_integration",
)

APPROVAL_HANDLERS = _handlers_mod.APPROVAL_HANDLERS
on_approval_complete = _handlers_mod.on_approval_complete
AGCM_ENTITY_TYPES = _integration_mod.AGCM_ENTITY_TYPES
check_approval = _integration_mod.check_approval
submit_for_approval = _integration_mod.submit_for_approval


def _uid():
    return uuid.uuid4().hex[:8]


def _ensure_approval_tables(db):
    """Check if approval tables exist (base_automation loaded)."""
    result = db.execute(
        text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'approval_chains')")
    ).scalar()
    return result


# ---------------------------------------------------------------------------
# Handler Registry Tests
# ---------------------------------------------------------------------------

class TestHandlerRegistry:

    def test_all_entity_types_have_handlers(self):
        for et in AGCM_ENTITY_TYPES:
            if et == "submittal":
                continue  # submittal has its own internal chain
            assert et in APPROVAL_HANDLERS, f"Missing handler for {et}"

    def test_handler_registry_values_are_callable(self):
        for et, handler in APPROVAL_HANDLERS.items():
            assert callable(handler), f"Handler for {et} is not callable"


# ---------------------------------------------------------------------------
# No-Chain Auto-Approve Tests (Backward Compatibility)
# ---------------------------------------------------------------------------

class TestNoChainAutoApprove:
    """When no approval chain is configured, approve methods should auto-approve."""

    def test_approve_po_no_chain(self, db, company_id, user_id, load_model):
        Project = load_model("agcm", "project", "Project")
        PurchaseOrder = load_model("agcm_procurement", "purchase_order", "PurchaseOrder")
        PurchaseOrderStatus = load_model("agcm_procurement", "purchase_order", "PurchaseOrderStatus")

        proj = Project(
            company_id=company_id, name=f"Test-{_uid()}", ref_number=f"TP-{_uid()}",
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            status="new", owner_id=user_id,
        )
        db.add(proj)
        db.flush()

        po = PurchaseOrder(
            company_id=company_id, project_id=proj.id,
            po_number=f"PO-{_uid()}", vendor_name="Test Vendor",
            status=PurchaseOrderStatus.DRAFT.value, created_by=user_id,
        )
        db.add(po)
        db.flush()

        # submit_for_approval returns None when no chain configured
        result = submit_for_approval(db, "purchase_order", po.id, user_id, company_id)
        assert result is None

    def test_approve_estimate_no_chain(self, db, company_id, user_id, load_model):
        Project = load_model("agcm", "project", "Project")
        Estimate = load_model("agcm_estimate", "estimate", "Estimate")
        EstimateStatus = load_model("agcm_estimate", "estimate", "EstimateStatus")

        proj = Project(
            company_id=company_id, name=f"Test-{_uid()}", ref_number=f"TP-{_uid()}",
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            status="new", owner_id=user_id,
        )
        db.add(proj)
        db.flush()

        est = Estimate(
            company_id=company_id, project_id=proj.id,
            name=f"Est-{_uid()}", status=EstimateStatus.DRAFT.value,
            created_by=user_id,
        )
        db.add(est)
        db.flush()

        result = submit_for_approval(db, "estimate", est.id, user_id, company_id)
        assert result is None


# ---------------------------------------------------------------------------
# Approval Completion Handler Tests
# ---------------------------------------------------------------------------

class TestApprovalHandlers:

    def test_po_handler_sets_approved(self, db, company_id, user_id, load_model):
        Project = load_model("agcm", "project", "Project")
        PurchaseOrder = load_model("agcm_procurement", "purchase_order", "PurchaseOrder")
        PurchaseOrderStatus = load_model("agcm_procurement", "purchase_order", "PurchaseOrderStatus")

        proj = Project(
            company_id=company_id, name=f"Test-{_uid()}", ref_number=f"TP-{_uid()}",
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            status="new", owner_id=user_id,
        )
        db.add(proj)
        db.flush()

        po = PurchaseOrder(
            company_id=company_id, project_id=proj.id,
            po_number=f"PO-{_uid()}", vendor_name="Test Vendor",
            status=PurchaseOrderStatus.PENDING_APPROVAL.value, created_by=user_id,
        )
        db.add(po)
        db.flush()

        result = on_approval_complete(db, "purchase_order", po.id, user_id, "APPROVED")
        assert result is True
        db.flush()
        db.refresh(po)
        assert po.status == PurchaseOrderStatus.APPROVED.value
        assert po.approved_by == user_id
        assert po.approved_date == date.today()

    def test_po_handler_sets_rejected(self, db, company_id, user_id, load_model):
        Project = load_model("agcm", "project", "Project")
        PurchaseOrder = load_model("agcm_procurement", "purchase_order", "PurchaseOrder")
        PurchaseOrderStatus = load_model("agcm_procurement", "purchase_order", "PurchaseOrderStatus")

        proj = Project(
            company_id=company_id, name=f"Test-{_uid()}", ref_number=f"TP-{_uid()}",
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            status="new", owner_id=user_id,
        )
        db.add(proj)
        db.flush()

        po = PurchaseOrder(
            company_id=company_id, project_id=proj.id,
            po_number=f"PO-{_uid()}", vendor_name="Test Vendor",
            status=PurchaseOrderStatus.PENDING_APPROVAL.value, created_by=user_id,
        )
        db.add(po)
        db.flush()

        result = on_approval_complete(db, "purchase_order", po.id, user_id, "REJECTED")
        assert result is True
        db.flush()
        db.refresh(po)
        assert po.status == PurchaseOrderStatus.REJECTED.value

    def test_co_handler_updates_budget(self, db, company_id, user_id, load_model):
        Project = load_model("agcm", "project", "Project")
        ChangeOrder = load_model("agcm_change_order", "change_order", "ChangeOrder")
        Budget = load_model("agcm_finance", "budget", "Budget")

        proj = Project(
            company_id=company_id, name=f"Test-{_uid()}", ref_number=f"TP-{_uid()}",
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            status="new", owner_id=user_id,
        )
        db.add(proj)
        db.flush()

        co = ChangeOrder(
            company_id=company_id, project_id=proj.id,
            sequence_name=f"CO-{_uid()}", title="Test CO",
            status="pending_approval", cost_impact=5000.0,
            created_by=user_id,
        )
        db.add(co)
        db.flush()

        result = on_approval_complete(db, "change_order", co.id, user_id, "APPROVED")
        assert result is True
        db.flush()
        db.refresh(co)
        assert co.status == "approved"

        # Verify budget line was created
        budget_line = (
            db.query(Budget)
            .filter(
                Budget.project_id == proj.id,
                Budget.description.ilike("%Approved Change Orders%"),
            )
            .first()
        )
        assert budget_line is not None
        assert budget_line.committed_amount == 5000.0

    def test_estimate_handler(self, db, company_id, user_id, load_model):
        Project = load_model("agcm", "project", "Project")
        Estimate = load_model("agcm_estimate", "estimate", "Estimate")
        EstimateStatus = load_model("agcm_estimate", "estimate", "EstimateStatus")

        proj = Project(
            company_id=company_id, name=f"Test-{_uid()}", ref_number=f"TP-{_uid()}",
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            status="new", owner_id=user_id,
        )
        db.add(proj)
        db.flush()

        est = Estimate(
            company_id=company_id, project_id=proj.id,
            name=f"Est-{_uid()}", status=EstimateStatus.PENDING_APPROVAL.value,
            created_by=user_id,
        )
        db.add(est)
        db.flush()

        result = on_approval_complete(db, "estimate", est.id, user_id, "APPROVED")
        assert result is True
        db.flush()
        db.refresh(est)
        assert est.status == EstimateStatus.APPROVED.value

    def test_vendor_bill_consistency_fix(self, db, company_id, user_id, load_model):
        """Verify approved_by and approved_date are now set for vendor bills."""
        Project = load_model("agcm", "project", "Project")
        VendorBill = load_model("agcm_procurement", "vendor_bill", "VendorBill")
        VendorBillStatus = load_model("agcm_procurement", "vendor_bill", "VendorBillStatus")

        proj = Project(
            company_id=company_id, name=f"Test-{_uid()}", ref_number=f"TP-{_uid()}",
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            status="new", owner_id=user_id,
        )
        db.add(proj)
        db.flush()

        bill = VendorBill(
            company_id=company_id, project_id=proj.id,
            vendor_name="Test Vendor", status=VendorBillStatus.PENDING_APPROVAL.value,
            created_by=user_id,
        )
        db.add(bill)
        db.flush()

        result = on_approval_complete(db, "vendor_bill", bill.id, user_id, "APPROVED")
        assert result is True
        db.flush()
        db.refresh(bill)
        assert bill.approved_by == user_id
        assert bill.approved_date == date.today()

    def test_unknown_entity_type_returns_false(self, db):
        result = on_approval_complete(db, "unknown_type", 999, 1, "APPROVED")
        assert result is False
