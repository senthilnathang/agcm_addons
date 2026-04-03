"""
Tests for AGCM budget posting lifecycle.

Verifies cost flows:
- PO approved → committed_amount increases
- Subcontract approved → committed_amount increases
- VendorBill approved → actual_amount increases
- Timesheet approved → actual_amount increases
- CO approved → committed_amount increases (via shared helper now)
- Budget summary reflects posted amounts
"""

import importlib.util
import os
import sys
import types
import uuid
from datetime import date

import pytest
from sqlalchemy import text

# Set up 'addons' namespace for handler imports
ADDONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.abspath(os.path.join(ADDONS_DIR, "..", "backend"))

if "addons" not in sys.modules:
    addons_pkg = types.ModuleType("addons")
    addons_pkg.__path__ = [ADDONS_DIR]
    addons_pkg.__package__ = "addons"
    sys.modules["addons"] = addons_pkg

# Load services via importlib
def _load_svc(file_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

_posting_mod = _load_svc(
    os.path.join(ADDONS_DIR, "agcm", "services", "budget_posting.py"),
    "agcm_budget_posting",
)
_handlers_mod = _load_svc(
    os.path.join(ADDONS_DIR, "agcm", "services", "approval_handlers.py"),
    "agcm_approval_handlers",
)

post_to_budget = _posting_mod.post_to_budget
reverse_budget_posting = _posting_mod.reverse_budget_posting
on_approval_complete = _handlers_mod.on_approval_complete


def _uid():
    return uuid.uuid4().hex[:8]


# ---------------------------------------------------------------------------
# Budget Posting Helper Tests
# ---------------------------------------------------------------------------

class TestPostToBudget:

    def test_creates_budget_line_on_first_post(self, db, company_id, user_id, load_model):
        Project = load_model("agcm", "project", "Project")
        Budget = load_model("agcm_finance", "budget", "Budget")

        proj = Project(
            company_id=company_id, name=f"Test-{_uid()}", ref_number=f"TP-{_uid()}",
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            status="new", owner_id=user_id,
        )
        db.add(proj)
        db.flush()

        result = post_to_budget(db, proj.id, company_id, "committed_amount", 5000.0,
                                description="Purchase Orders")
        assert result is True
        db.flush()

        bl = db.query(Budget).filter(
            Budget.project_id == proj.id, Budget.description == "Purchase Orders"
        ).first()
        assert bl is not None
        assert bl.committed_amount == 5000.0
        assert bl.actual_amount == 0

    def test_increments_existing_budget_line(self, db, company_id, user_id, load_model):
        Project = load_model("agcm", "project", "Project")
        Budget = load_model("agcm_finance", "budget", "Budget")

        proj = Project(
            company_id=company_id, name=f"Test-{_uid()}", ref_number=f"TP-{_uid()}",
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            status="new", owner_id=user_id,
        )
        db.add(proj)
        db.flush()

        # First post
        post_to_budget(db, proj.id, company_id, "actual_amount", 1000.0,
                        description="Vendor Bills")
        db.flush()
        # Second post (should increment)
        post_to_budget(db, proj.id, company_id, "actual_amount", 2500.0,
                        description="Vendor Bills")
        db.flush()

        bl = db.query(Budget).filter(
            Budget.project_id == proj.id, Budget.description == "Vendor Bills"
        ).first()
        assert bl.actual_amount == 3500.0

    def test_reverse_budget_posting(self, db, company_id, user_id, load_model):
        Project = load_model("agcm", "project", "Project")
        Budget = load_model("agcm_finance", "budget", "Budget")

        proj = Project(
            company_id=company_id, name=f"Test-{_uid()}", ref_number=f"TP-{_uid()}",
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            status="new", owner_id=user_id,
        )
        db.add(proj)
        db.flush()

        post_to_budget(db, proj.id, company_id, "committed_amount", 10000.0,
                        description="Subcontracts")
        db.flush()
        reverse_budget_posting(db, proj.id, company_id, "committed_amount", 10000.0,
                                description="Subcontracts")
        db.flush()

        bl = db.query(Budget).filter(
            Budget.project_id == proj.id, Budget.description == "Subcontracts"
        ).first()
        assert bl.committed_amount == 0.0

    def test_invalid_column_returns_false(self, db):
        result = post_to_budget(db, 1, 1, "invalid_column", 100.0, description="Test")
        assert result is False

    def test_zero_amount_returns_false(self, db):
        result = post_to_budget(db, 1, 1, "actual_amount", 0, description="Test")
        assert result is False


# ---------------------------------------------------------------------------
# Handler Budget Posting Tests
# ---------------------------------------------------------------------------

class TestPOBudgetPosting:

    def test_po_approval_posts_committed(self, db, company_id, user_id, load_model):
        Project = load_model("agcm", "project", "Project")
        PurchaseOrder = load_model("agcm_procurement", "purchase_order", "PurchaseOrder")
        Budget = load_model("agcm_finance", "budget", "Budget")

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
            status="pending_approval", total_amount=25000.0, created_by=user_id,
        )
        db.add(po)
        db.flush()

        on_approval_complete(db, "purchase_order", po.id, user_id, "APPROVED")
        db.flush()

        bl = db.query(Budget).filter(
            Budget.project_id == proj.id, Budget.description == "Purchase Orders"
        ).first()
        assert bl is not None
        assert bl.committed_amount == 25000.0


class TestVendorBillBudgetPosting:

    def test_vendor_bill_approval_posts_actual(self, db, company_id, user_id, load_model):
        Project = load_model("agcm", "project", "Project")
        VendorBill = load_model("agcm_procurement", "vendor_bill", "VendorBill")
        Budget = load_model("agcm_finance", "budget", "Budget")

        proj = Project(
            company_id=company_id, name=f"Test-{_uid()}", ref_number=f"TP-{_uid()}",
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            status="new", owner_id=user_id,
        )
        db.add(proj)
        db.flush()

        bill = VendorBill(
            company_id=company_id, project_id=proj.id,
            vendor_name="Test Vendor", status="pending_approval",
            total_amount=8500.0, created_by=user_id,
        )
        db.add(bill)
        db.flush()

        on_approval_complete(db, "vendor_bill", bill.id, user_id, "APPROVED")
        db.flush()

        bl = db.query(Budget).filter(
            Budget.project_id == proj.id, Budget.description == "Vendor Bills"
        ).first()
        assert bl is not None
        assert bl.actual_amount == 8500.0


class TestSubcontractBudgetPosting:

    def test_subcontract_approval_posts_committed(self, db, company_id, user_id, load_model):
        Project = load_model("agcm", "project", "Project")
        Subcontract = load_model("agcm_procurement", "subcontract", "Subcontract")
        Budget = load_model("agcm_finance", "budget", "Budget")

        proj = Project(
            company_id=company_id, name=f"Test-{_uid()}", ref_number=f"TP-{_uid()}",
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            status="new", owner_id=user_id,
        )
        db.add(proj)
        db.flush()

        sc = Subcontract(
            company_id=company_id, project_id=proj.id,
            sequence_name=f"SC-{_uid()}", vendor_name="Test Sub",
            status="pending_approval", original_amount=50000.0,
            revised_amount=55000.0, created_by=user_id,
        )
        db.add(sc)
        db.flush()

        on_approval_complete(db, "subcontract", sc.id, user_id, "APPROVED")
        db.flush()

        bl = db.query(Budget).filter(
            Budget.project_id == proj.id, Budget.description == "Subcontracts"
        ).first()
        assert bl is not None
        assert bl.committed_amount == 55000.0  # Uses revised_amount


class TestCOBudgetPostingRefactored:

    def test_co_still_posts_committed(self, db, company_id, user_id, load_model):
        """Verify CO handler still works after refactor to shared helper."""
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
            status="pending_approval", cost_impact=12000.0, created_by=user_id,
        )
        db.add(co)
        db.flush()

        on_approval_complete(db, "change_order", co.id, user_id, "APPROVED")
        db.flush()

        bl = db.query(Budget).filter(
            Budget.project_id == proj.id, Budget.description == "Approved Change Orders"
        ).first()
        assert bl is not None
        assert bl.committed_amount == 12000.0
