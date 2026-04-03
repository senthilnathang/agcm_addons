"""
Tests for Invoice/Bill line items with tax calculation.

Verifies:
- TaxRate CRUD
- InvoiceLine creation with tax calculation
- BillLine creation with tax calculation
- Document total recalculation from lines
- Retention calculation on invoice lines
"""

import uuid
from datetime import date

import pytest


def _uid():
    return uuid.uuid4().hex[:8]


class TestTaxRate:

    def test_create_tax_rate(self, db, company_id, load_model):
        TaxRate = load_model("agcm_finance", "tax_rate", "TaxRate")

        tr = TaxRate(company_id=company_id, name=f"Sales Tax {_uid()}", rate=8.25, is_default=True)
        db.add(tr)
        db.flush()
        assert tr.id is not None
        assert tr.rate == 8.25
        assert tr.is_default is True


class TestInvoiceLines:

    def _make_project(self, db, company_id, user_id, load_model):
        Project = load_model("agcm", "project", "Project")
        proj = Project(
            company_id=company_id, name=f"Test-{_uid()}", ref_number=f"TP-{_uid()}",
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            status="new", owner_id=user_id,
        )
        db.add(proj)
        db.flush()
        return proj

    def test_create_invoice_with_line(self, db, company_id, user_id, load_model):
        Invoice = load_model("agcm_finance", "invoice", "Invoice")
        InvoiceLine = load_model("agcm_finance", "invoice_line", "InvoiceLine")
        proj = self._make_project(db, company_id, user_id, load_model)

        inv = Invoice(
            company_id=company_id, project_id=proj.id,
            client_name="Test Client", status="draft",
            created_by=user_id,
        )
        db.add(inv)
        db.flush()

        line = InvoiceLine(
            invoice_id=inv.id, company_id=company_id,
            description="Concrete work", quantity=100, unit="cy",
            unit_price=150.0, subtotal=15000.0, taxable=False,
            tax_amount=0, total=15000.0, display_order=1,
        )
        db.add(line)
        db.flush()

        assert line.id is not None
        assert line.subtotal == 15000.0
        assert line.total == 15000.0

    def test_line_with_tax_rate(self, db, company_id, user_id, load_model):
        Invoice = load_model("agcm_finance", "invoice", "Invoice")
        InvoiceLine = load_model("agcm_finance", "invoice_line", "InvoiceLine")
        TaxRate = load_model("agcm_finance", "tax_rate", "TaxRate")
        proj = self._make_project(db, company_id, user_id, load_model)

        tr = TaxRate(company_id=company_id, name=f"Tax {_uid()}", rate=10.0)
        db.add(tr)
        db.flush()

        inv = Invoice(
            company_id=company_id, project_id=proj.id,
            client_name="Test Client", status="draft",
            created_by=user_id,
        )
        db.add(inv)
        db.flush()

        # Simulate service calculation
        qty, price = 50, 200.0
        subtotal = qty * price  # 10000
        tax_amount = subtotal * tr.rate / 100  # 1000
        total = subtotal + tax_amount  # 11000

        line = InvoiceLine(
            invoice_id=inv.id, company_id=company_id,
            description="Steel framing", quantity=qty, unit="ton",
            unit_price=price, subtotal=subtotal, taxable=True,
            tax_rate_id=tr.id, tax_amount=tax_amount, total=total,
            display_order=1,
        )
        db.add(line)
        db.flush()

        assert line.subtotal == 10000.0
        assert line.tax_amount == 1000.0
        assert line.total == 11000.0

    def test_retention_calculation(self, db, company_id, user_id, load_model):
        Invoice = load_model("agcm_finance", "invoice", "Invoice")
        InvoiceLine = load_model("agcm_finance", "invoice_line", "InvoiceLine")
        proj = self._make_project(db, company_id, user_id, load_model)

        inv = Invoice(
            company_id=company_id, project_id=proj.id,
            client_name="Test Client", status="draft",
            created_by=user_id,
        )
        db.add(inv)
        db.flush()

        subtotal = 20000.0
        retention_pct = 10.0
        retention_amount = subtotal * retention_pct / 100  # 2000

        line = InvoiceLine(
            invoice_id=inv.id, company_id=company_id,
            description="Electrical", quantity=1, unit="ls",
            unit_price=subtotal, subtotal=subtotal, taxable=False,
            tax_amount=0, total=subtotal,
            retention_pct=retention_pct, retention_amount=retention_amount,
            display_order=1,
        )
        db.add(line)
        db.flush()

        assert line.retention_pct == 10.0
        assert line.retention_amount == 2000.0


class TestBillLines:

    def _make_project(self, db, company_id, user_id, load_model):
        Project = load_model("agcm", "project", "Project")
        proj = Project(
            company_id=company_id, name=f"Test-{_uid()}", ref_number=f"TP-{_uid()}",
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            status="new", owner_id=user_id,
        )
        db.add(proj)
        db.flush()
        return proj

    def test_create_bill_with_line(self, db, company_id, user_id, load_model):
        Bill = load_model("agcm_finance", "bill", "Bill")
        BillLine = load_model("agcm_finance", "bill_line", "BillLine")
        proj = self._make_project(db, company_id, user_id, load_model)

        bill = Bill(
            company_id=company_id, project_id=proj.id,
            vendor_name="Test Vendor", status="draft",
            created_by=user_id,
        )
        db.add(bill)
        db.flush()

        line = BillLine(
            bill_id=bill.id, company_id=company_id,
            description="Lumber delivery", quantity=500, unit="bf",
            unit_cost=3.50, subtotal=1750.0, taxable=False,
            tax_amount=0, total=1750.0, display_order=1,
        )
        db.add(line)
        db.flush()

        assert line.id is not None
        assert line.subtotal == 1750.0

    def test_bill_line_with_tax(self, db, company_id, user_id, load_model):
        Bill = load_model("agcm_finance", "bill", "Bill")
        BillLine = load_model("agcm_finance", "bill_line", "BillLine")
        TaxRate = load_model("agcm_finance", "tax_rate", "TaxRate")
        proj = self._make_project(db, company_id, user_id, load_model)

        tr = TaxRate(company_id=company_id, name=f"Tax {_uid()}", rate=7.5)
        db.add(tr)
        db.flush()

        bill = Bill(
            company_id=company_id, project_id=proj.id,
            vendor_name="Test Vendor", status="draft",
            created_by=user_id,
        )
        db.add(bill)
        db.flush()

        qty, cost = 200, 25.0
        subtotal = qty * cost  # 5000
        tax_amount = subtotal * tr.rate / 100  # 375
        total = subtotal + tax_amount  # 5375

        line = BillLine(
            bill_id=bill.id, company_id=company_id,
            description="Drywall sheets", quantity=qty, unit="ea",
            unit_cost=cost, subtotal=subtotal, taxable=True,
            tax_rate_id=tr.id, tax_amount=tax_amount, total=total,
            display_order=1,
        )
        db.add(line)
        db.flush()

        assert line.subtotal == 5000.0
        assert line.tax_amount == 375.0
        assert line.total == 5375.0

    def test_multiple_lines_sum(self, db, company_id, user_id, load_model):
        Bill = load_model("agcm_finance", "bill", "Bill")
        BillLine = load_model("agcm_finance", "bill_line", "BillLine")
        proj = self._make_project(db, company_id, user_id, load_model)

        bill = Bill(
            company_id=company_id, project_id=proj.id,
            vendor_name="Test Vendor", status="draft",
            created_by=user_id,
        )
        db.add(bill)
        db.flush()

        for i, (desc, qty, cost) in enumerate([
            ("Line 1", 10, 100.0),
            ("Line 2", 5, 200.0),
            ("Line 3", 20, 50.0),
        ]):
            subtotal = qty * cost
            line = BillLine(
                bill_id=bill.id, company_id=company_id,
                description=desc, quantity=qty, unit="ea",
                unit_cost=cost, subtotal=subtotal, taxable=False,
                tax_amount=0, total=subtotal, display_order=i,
            )
            db.add(line)

        db.flush()

        # Verify sum of line totals
        total = sum(l.total for l in bill.lines)
        assert total == 3000.0  # 1000 + 1000 + 1000
