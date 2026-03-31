"""Tests for agcm_portal module."""
import pytest
from datetime import date


@pytest.fixture
def M(load_model):
    return {
        "Selection": load_model("agcm_portal", "selection", "Selection"),
        "SelectionOption": load_model("agcm_portal", "selection", "SelectionOption"),
        "BidPackage": load_model("agcm_portal", "bid", "BidPackage"),
        "BidSubmission": load_model("agcm_portal", "bid", "BidSubmission"),
        "PortalConfig": load_model("agcm_portal", "portal_config", "PortalConfig"),
    }


class TestSelection:
    def test_create_selection(self, db, M, company_id, project_ids):
        s = M["Selection"](company_id=company_id, project_id=project_ids[0], name="Kitchen Countertops", category="countertops", status="pending", budget_amount=5000)
        db.add(s); db.flush()
        assert s.id and s.category == "countertops"

    def test_selection_options(self, db, M, company_id, project_ids):
        s = M["Selection"](company_id=company_id, project_id=project_ids[0], name="Flooring", category="flooring", status="presented")
        db.add(s); db.flush()
        for i, (name, price) in enumerate([("Hardwood Oak", 12.50), ("LVP", 6.00), ("Tile", 8.75)]):
            opt = M["SelectionOption"](selection_id=s.id, company_id=company_id, name=name, price=price, unit="sf", is_recommended=(i == 0), display_order=i)
            db.add(opt)
        db.flush()
        count = db.query(M["SelectionOption"]).filter(M["SelectionOption"].selection_id == s.id).count()
        assert count == 3

    def test_selection_approval(self, db, M, company_id, project_ids):
        s = M["Selection"](company_id=company_id, project_id=project_ids[0], name="Paint Color", category="paint", status="pending", budget_amount=2000)
        db.add(s); db.flush()
        s.status = "approved"; s.selected_amount = 2200; s.budget_impact = 200; s.decided_date = date.today(); db.flush()
        assert s.budget_impact == 200


class TestBidPackage:
    def test_create_bid_package(self, db, M, company_id, project_ids):
        bp = M["BidPackage"](company_id=company_id, project_id=project_ids[0], sequence_name="BID00001", name="Electrical Package", trade="electrical", status="open", due_date=date(2025, 5, 1))
        db.add(bp); db.flush()
        assert bp.id and bp.trade == "electrical"

    def test_bid_submissions(self, db, M, company_id, project_ids):
        bp = M["BidPackage"](company_id=company_id, project_id=project_ids[0], sequence_name="BID00002", name="Plumbing", status="open")
        db.add(bp); db.flush()
        sub = M["BidSubmission"](bid_package_id=bp.id, company_id=company_id, vendor_name="Pro Plumbing", total_amount=85000, status="submitted", submitted_date=date.today())
        db.add(sub); db.flush()
        sub.status = "awarded"; sub.is_awarded = True; db.flush()
        assert sub.is_awarded is True


class TestPortalConfig:
    def test_create_config(self, db, M, company_id, project_ids):
        cfg = M["PortalConfig"](company_id=company_id, project_id=project_ids[0], client_portal_enabled=True, show_budget=False, show_schedule=True)
        db.add(cfg); db.flush()
        assert cfg.client_portal_enabled is True and cfg.show_budget is False
