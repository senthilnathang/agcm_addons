"""Tests for agcm_procurement module — Purchase Orders, Subcontracts, Vendor Bills."""

import pytest
from datetime import date


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def models(load_model):
    """Load all procurement models."""
    return {
        "PurchaseOrder": load_model("agcm_procurement", "purchase_order", "PurchaseOrder"),
        "PurchaseOrderLine": load_model("agcm_procurement", "purchase_order", "PurchaseOrderLine"),
        "Subcontract": load_model("agcm_procurement", "subcontract", "Subcontract"),
        "SubcontractSOVLine": load_model("agcm_procurement", "subcontract", "SubcontractSOVLine"),
        "SubcontractComplianceDoc": load_model("agcm_procurement", "subcontract", "SubcontractComplianceDoc"),
        "VendorBill": load_model("agcm_procurement", "vendor_bill", "VendorBill"),
        "VendorBillLine": load_model("agcm_procurement", "vendor_bill", "VendorBillLine"),
        "VendorBillPayment": load_model("agcm_procurement", "vendor_bill", "VendorBillPayment"),
    }


# ---------------------------------------------------------------------------
# Purchase Order Tests
# ---------------------------------------------------------------------------

class TestPurchaseOrder:

    def test_create_purchase_order(self, db, models, company_id, user_id, project_ids):
        PO = models["PurchaseOrder"]
        po = PO(
            company_id=company_id, project_id=project_ids[0],
            sequence_name="PO00001", po_number="PO-01-001",
            vendor_name="ABC Building Supply", status="draft",
            subtotal=50000, tax_amount=4125, total_amount=54125,
            issue_date=date(2025, 3, 1), created_by=user_id,
        )
        db.add(po); db.flush()
        assert po.id is not None
        assert po.vendor_name == "ABC Building Supply"
        assert po.status == "draft"

    def test_po_with_lines(self, db, models, company_id, user_id, project_ids):
        PO = models["PurchaseOrder"]
        Line = models["PurchaseOrderLine"]
        po = PO(
            company_id=company_id, project_id=project_ids[0],
            sequence_name="PO00002", vendor_name="Steel Co",
            status="draft", created_by=user_id,
        )
        db.add(po); db.flush()

        items = [
            ("Rebar #5", "material", 500, "lf", 1.25),
            ("Concrete 4000psi", "material", 100, "cy", 135.00),
            ("Crane rental", "equipment", 5, "day", 2500.00),
        ]
        total = 0
        for desc, itype, qty, unit, uc in items:
            tc = qty * uc
            total += tc
            line = Line(
                po_id=po.id, company_id=company_id,
                description=desc, item_type=itype,
                quantity=qty, unit=unit, unit_cost=uc, total_cost=tc,
            )
            db.add(line)
        db.flush()

        po.subtotal = total
        po.total_amount = total
        db.flush()
        assert po.subtotal == 500 * 1.25 + 100 * 135 + 5 * 2500

    def test_po_status_workflow(self, db, models, company_id, user_id, project_ids):
        PO = models["PurchaseOrder"]
        po = PO(
            company_id=company_id, project_id=project_ids[0],
            sequence_name="PO00003", vendor_name="Test Vendor",
            status="draft", created_by=user_id,
        )
        db.add(po); db.flush()

        po.status = "pending_approval"; db.flush()
        assert po.status == "pending_approval"

        po.status = "approved"; po.approved_by = user_id; po.approved_date = date.today()
        db.flush()
        assert po.status == "approved"
        assert po.approved_by == user_id

    def test_po_receive_delivery(self, db, models, company_id, user_id, project_ids):
        PO = models["PurchaseOrder"]
        Line = models["PurchaseOrderLine"]
        po = PO(
            company_id=company_id, project_id=project_ids[0],
            sequence_name="PO00004", vendor_name="Lumber Yard",
            status="approved", created_by=user_id,
        )
        db.add(po); db.flush()
        line = Line(
            po_id=po.id, company_id=company_id,
            description="2x4 Studs", quantity=1000, unit="ea",
            unit_cost=3.50, total_cost=3500, received_qty=0,
        )
        db.add(line); db.flush()

        line.received_qty = 600; db.flush()
        assert line.received_qty == 600
        po.status = "partially_received"; db.flush()
        assert po.status == "partially_received"

    def test_delete_po_cascades(self, db, models, company_id, user_id, project_ids):
        PO = models["PurchaseOrder"]
        Line = models["PurchaseOrderLine"]
        po = PO(
            company_id=company_id, project_id=project_ids[0],
            sequence_name="PO00005", vendor_name="Cascade Test",
            status="draft", created_by=user_id,
        )
        db.add(po); db.flush()
        line = Line(po_id=po.id, company_id=company_id, description="Item", quantity=1, unit_cost=100, total_cost=100)
        db.add(line); db.flush()
        line_id = line.id

        db.delete(po); db.flush()
        assert db.query(Line).filter(Line.id == line_id).first() is None


# ---------------------------------------------------------------------------
# Subcontract Tests
# ---------------------------------------------------------------------------

class TestSubcontract:

    def test_create_subcontract(self, db, models, company_id, user_id, project_ids):
        SC = models["Subcontract"]
        sc = SC(
            company_id=company_id, project_id=project_ids[0],
            sequence_name="SC00001", contract_number="SC-01-001",
            vendor_name="Elite Electrical", status="draft",
            scope_of_work="Complete electrical rough-in for floors 1-3",
            original_amount=185000, revised_amount=185000,
            retainage_pct=10.0, created_by=user_id,
        )
        db.add(sc); db.flush()
        assert sc.id is not None
        assert sc.retainage_pct == 10.0

    def test_sov_lines(self, db, models, company_id, user_id, project_ids):
        SC = models["Subcontract"]
        SOV = models["SubcontractSOVLine"]
        sc = SC(
            company_id=company_id, project_id=project_ids[0],
            sequence_name="SC00002", vendor_name="Plumbing Pro",
            status="active", original_amount=120000, revised_amount=120000,
            created_by=user_id,
        )
        db.add(sc); db.flush()

        sov = SOV(
            subcontract_id=sc.id, company_id=company_id,
            description="Underslab plumbing", scheduled_value=45000,
            billed_previous=20000, billed_current=10000, stored_materials=5000,
        )
        db.add(sov); db.flush()

        sov.total_completed = sov.billed_previous + sov.billed_current + sov.stored_materials
        sov.pct_complete = round(sov.total_completed / sov.scheduled_value * 100, 1)
        sov.balance_to_finish = sov.scheduled_value - sov.total_completed
        db.flush()

        assert sov.total_completed == 35000
        assert sov.pct_complete == 77.8
        assert sov.balance_to_finish == 10000

    def test_compliance_doc(self, db, models, company_id, user_id, project_ids):
        SC = models["Subcontract"]
        Doc = models["SubcontractComplianceDoc"]
        sc = SC(
            company_id=company_id, project_id=project_ids[0],
            sequence_name="SC00003", vendor_name="HVAC Corp",
            status="draft", original_amount=95000, created_by=user_id,
        )
        db.add(sc); db.flush()

        doc = Doc(
            subcontract_id=sc.id, company_id=company_id,
            doc_type="insurance_coi", status="submitted",
            description="General Liability COI",
            expiration_date=date(2026, 12, 31),
        )
        db.add(doc); db.flush()
        assert doc.doc_type == "insurance_coi"
        assert doc.status == "submitted"

    def test_subcontract_approval(self, db, models, company_id, user_id, project_ids):
        SC = models["Subcontract"]
        sc = SC(
            company_id=company_id, project_id=project_ids[0],
            sequence_name="SC00004", vendor_name="Approval Test",
            status="draft", original_amount=50000, created_by=user_id,
        )
        db.add(sc); db.flush()
        sc.status = "pending_approval"; db.flush()
        sc.status = "approved"; sc.approved_by = user_id; sc.approved_date = date.today()
        db.flush()
        assert sc.status == "approved"

    def test_delete_subcontract_cascades(self, db, models, company_id, user_id, project_ids):
        SC = models["Subcontract"]
        SOV = models["SubcontractSOVLine"]
        Doc = models["SubcontractComplianceDoc"]
        sc = SC(
            company_id=company_id, project_id=project_ids[0],
            sequence_name="SC00005", vendor_name="Cascade",
            status="draft", original_amount=10000, created_by=user_id,
        )
        db.add(sc); db.flush()
        sov = SOV(subcontract_id=sc.id, company_id=company_id, description="Line 1", scheduled_value=5000)
        doc = Doc(subcontract_id=sc.id, company_id=company_id, doc_type="w9", status="required", description="W-9")
        db.add_all([sov, doc]); db.flush()
        sov_id, doc_id = sov.id, doc.id

        db.delete(sc); db.flush()
        assert db.query(SOV).filter(SOV.id == sov_id).first() is None
        assert db.query(Doc).filter(Doc.id == doc_id).first() is None


# ---------------------------------------------------------------------------
# Vendor Bill Tests
# ---------------------------------------------------------------------------

class TestVendorBill:

    def test_create_vendor_bill(self, db, models, company_id, user_id, project_ids):
        VB = models["VendorBill"]
        vb = VB(
            company_id=company_id, project_id=project_ids[0],
            sequence_name="VB00001", bill_number="INV-2025-001",
            vendor_name="Material Supply Co", record_type="bill",
            status="draft", subtotal=25000, tax_amount=2062.50,
            total_amount=27062.50, balance_due=27062.50,
            issue_date=date(2025, 3, 15), due_date=date(2025, 4, 14),
            created_by=user_id,
        )
        db.add(vb); db.flush()
        assert vb.id is not None
        assert vb.record_type == "bill"

    def test_bill_with_lines(self, db, models, company_id, user_id, project_ids):
        VB = models["VendorBill"]
        Line = models["VendorBillLine"]
        vb = VB(
            company_id=company_id, project_id=project_ids[0],
            sequence_name="VB00002", vendor_name="Line Test",
            status="draft", created_by=user_id,
        )
        db.add(vb); db.flush()

        total = 0
        for i, (desc, qty, uc) in enumerate([
            ("Concrete delivery", 50, 135), ("Rebar delivery", 200, 1.50), ("Pump rental", 1, 2500),
        ]):
            amt = qty * uc; total += amt
            line = Line(
                bill_id=vb.id, company_id=company_id,
                description=desc, quantity=qty, unit_cost=uc, amount=amt,
                display_order=i,
            )
            db.add(line)
        db.flush()
        vb.subtotal = total; vb.total_amount = total; vb.balance_due = total
        db.flush()
        assert vb.subtotal == 50 * 135 + 200 * 1.50 + 2500

    def test_record_payment(self, db, models, company_id, user_id, project_ids):
        VB = models["VendorBill"]
        Pay = models["VendorBillPayment"]
        vb = VB(
            company_id=company_id, project_id=project_ids[0],
            sequence_name="VB00003", vendor_name="Payment Test",
            status="approved", total_amount=10000, balance_due=10000,
            paid_amount=0, created_by=user_id,
        )
        db.add(vb); db.flush()

        p1 = Pay(
            bill_id=vb.id, company_id=company_id,
            payment_date=date(2025, 4, 1), amount=6000,
            payment_method="check", reference_number="CHK-1234",
            recorded_by=user_id,
        )
        db.add(p1); db.flush()
        vb.paid_amount = 6000; vb.balance_due = 4000; vb.status = "partially_paid"
        db.flush()
        assert vb.paid_amount == 6000
        assert vb.balance_due == 4000

        p2 = Pay(
            bill_id=vb.id, company_id=company_id,
            payment_date=date(2025, 4, 15), amount=4000,
            payment_method="wire", recorded_by=user_id,
        )
        db.add(p2); db.flush()
        vb.paid_amount = 10000; vb.balance_due = 0; vb.status = "paid"
        db.flush()
        assert vb.status == "paid"
        assert vb.balance_due == 0

    def test_duplicate_detection(self, db, models, company_id, user_id, project_ids):
        VB = models["VendorBill"]
        vb1 = VB(
            company_id=company_id, project_id=project_ids[0],
            sequence_name="VB00004", vendor_name="Dup Vendor",
            vendor_invoice_ref="VINV-2025-100", status="approved",
            total_amount=5000, created_by=user_id,
        )
        db.add(vb1); db.flush()

        vb2 = VB(
            company_id=company_id, project_id=project_ids[0],
            sequence_name="VB00005", vendor_name="Dup Vendor",
            vendor_invoice_ref="VINV-2025-100", status="draft",
            total_amount=5000, duplicate_flag=True, duplicate_of_id=vb1.id,
            created_by=user_id,
        )
        db.add(vb2); db.flush()
        assert vb2.duplicate_flag is True
        assert vb2.duplicate_of_id == vb1.id

    def test_record_types(self, db, models, company_id, user_id, project_ids):
        VB = models["VendorBill"]
        for i, rt in enumerate(["bill", "expense", "vendor_credit"]):
            vb = VB(
                company_id=company_id, project_id=project_ids[0],
                sequence_name=f"VB0010{i}", vendor_name=f"{rt.title()} Vendor",
                record_type=rt, status="draft", total_amount=1000 * (i + 1),
                created_by=user_id,
            )
            db.add(vb)
        db.flush()
        count = db.query(VB).filter(
            VB.company_id == company_id,
            VB.sequence_name.like("VB0010%"),
        ).count()
        assert count == 3
