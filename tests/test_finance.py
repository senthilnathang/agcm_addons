"""Tests for the agcm_finance module — CostCode, Budget, Expense, Invoice, Bill models."""

import pytest
from datetime import date
from sqlalchemy import func


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cost_code(load_model):
    return load_model("agcm_finance", "cost_code", "CostCode")

def _budget(load_model):
    return load_model("agcm_finance", "budget", "Budget")

def _expense(load_model):
    return load_model("agcm_finance", "expense", "Expense")

def _expense_line(load_model):
    return load_model("agcm_finance", "expense", "ExpenseLine")

def _expense_status(load_model):
    return load_model("agcm_finance", "expense", "ExpenseStatus")

def _invoice(load_model):
    return load_model("agcm_finance", "invoice", "Invoice")

def _invoice_status(load_model):
    return load_model("agcm_finance", "invoice", "InvoiceStatus")

def _bill(load_model):
    return load_model("agcm_finance", "bill", "Bill")

def _bill_status(load_model):
    return load_model("agcm_finance", "bill", "BillStatus")


# ---------------------------------------------------------------------------
# CostCode tests
# ---------------------------------------------------------------------------

class TestCostCode:

    def test_create_cost_code(self, db, load_model, project_ids, company_id):
        CostCode = _cost_code(load_model)
        cc = CostCode(
            code="03-000",
            name="Concrete",
            category="Division 03",
            project_id=project_ids[0],
            company_id=company_id,
        )
        db.add(cc)
        db.flush()

        assert cc.id is not None
        assert cc.code == "03-000"
        assert cc.name == "Concrete"

    def test_cost_code_hierarchy(self, db, load_model, project_ids, company_id):
        CostCode = _cost_code(load_model)

        parent = CostCode(code="03-000", name="Concrete", project_id=project_ids[0], company_id=company_id)
        db.add(parent)
        db.flush()

        child = CostCode(code="03-100", name="Concrete Formwork", project_id=project_ids[0], company_id=company_id, parent_id=parent.id)
        db.add(child)
        db.flush()

        assert child.parent_id == parent.id


# ---------------------------------------------------------------------------
# Budget tests
# ---------------------------------------------------------------------------

class TestBudget:

    def test_create_budget(self, db, load_model, project_ids, company_id):
        Budget = _budget(load_model)

        budget = Budget(
            description="Concrete materials",
            planned_amount=150000.00,
            actual_amount=0.0,
            committed_amount=50000.00,
            project_id=project_ids[0],
            company_id=company_id,
        )
        db.add(budget)
        db.flush()

        assert budget.id is not None
        assert budget.planned_amount == 150000.00
        assert budget.committed_amount == 50000.00

    def test_budget_summary(self, db, load_model, project_ids, company_id):
        Budget = _budget(load_model)

        db.add(Budget(description="Line 1", planned_amount=100000, actual_amount=80000, committed_amount=10000, project_id=project_ids[0], company_id=company_id))
        db.add(Budget(description="Line 2", planned_amount=200000, actual_amount=150000, committed_amount=20000, project_id=project_ids[0], company_id=company_id))
        db.add(Budget(description="Line 3", planned_amount=50000, actual_amount=30000, committed_amount=5000, project_id=project_ids[0], company_id=company_id))
        db.flush()

        totals = db.query(
            func.sum(Budget.planned_amount),
            func.sum(Budget.actual_amount),
            func.sum(Budget.committed_amount),
        ).filter(Budget.project_id == project_ids[0]).one()

        assert totals[0] == 350000
        assert totals[1] == 260000
        assert totals[2] == 35000


# ---------------------------------------------------------------------------
# Expense tests
# ---------------------------------------------------------------------------

class TestExpense:

    def test_create_expense_with_lines(self, db, load_model, project_ids, company_id):
        Expense = _expense(load_model)
        ExpenseLine = _expense_line(load_model)

        exp = Expense(
            description="Site equipment rental",
            vendor="ABC Equipment Co",
            project_id=project_ids[0],
            company_id=company_id,
            sequence_name="EXP00001",
        )
        db.add(exp)
        db.flush()

        lines = [
            ExpenseLine(expense_id=exp.id, description="Excavator rental", quantity=5, unit="days", unit_cost=800, total_cost=4000, company_id=company_id),
            ExpenseLine(expense_id=exp.id, description="Crane rental", quantity=3, unit="days", unit_cost=1200, total_cost=3600, company_id=company_id),
        ]
        db.add_all(lines)
        db.flush()

        db.expire(exp)
        assert len(exp.lines) == 2
        assert exp.lines[0].description == "Excavator rental"

    def test_expense_sequence(self, db, load_model, project_ids, company_id):
        Expense = _expense(load_model)

        for i in range(1, 4):
            db.add(Expense(
                description=f"Expense {i}",
                project_id=project_ids[0],
                company_id=company_id,
                sequence_name=f"EXP{i:05d}",
            ))
        db.flush()

        exps = db.query(Expense).filter(Expense.project_id == project_ids[0]).order_by(Expense.id).all()
        assert exps[0].sequence_name == "EXP00001"
        assert exps[2].sequence_name == "EXP00003"

    def test_list_expenses_filter(self, db, load_model, project_ids, company_id):
        Expense = _expense(load_model)
        ExpenseStatus = _expense_status(load_model)

        db.add(Expense(description="Draft exp", project_id=project_ids[0], company_id=company_id, status=ExpenseStatus.DRAFT))
        db.add(Expense(description="Approved exp", project_id=project_ids[0], company_id=company_id, status=ExpenseStatus.APPROVED))
        db.add(Expense(description="Draft exp 2", project_id=project_ids[0], company_id=company_id, status=ExpenseStatus.DRAFT))
        db.flush()

        drafts = db.query(Expense).filter(Expense.status == ExpenseStatus.DRAFT).all()
        assert len(drafts) == 2

    def test_delete_expense_cascades_lines(self, db, load_model, project_ids, company_id):
        Expense = _expense(load_model)
        ExpenseLine = _expense_line(load_model)

        exp = Expense(description="Cascade exp", project_id=project_ids[0], company_id=company_id)
        db.add(exp)
        db.flush()

        line = ExpenseLine(expense_id=exp.id, description="Line 1", quantity=1, unit_cost=100, total_cost=100, company_id=company_id)
        db.add(line)
        db.flush()
        line_id = line.id

        db.delete(exp)
        db.flush()

        assert db.get(ExpenseLine, line_id) is None

    def test_expense_status_workflow(self, db, load_model, project_ids, company_id):
        Expense = _expense(load_model)
        ExpenseStatus = _expense_status(load_model)

        exp = Expense(description="Workflow", project_id=project_ids[0], company_id=company_id, status=ExpenseStatus.DRAFT)
        db.add(exp)
        db.flush()

        for st in [ExpenseStatus.SUBMITTED, ExpenseStatus.APPROVED, ExpenseStatus.PAID]:
            exp.status = st
            db.flush()
            assert exp.status == st


# ---------------------------------------------------------------------------
# Invoice tests
# ---------------------------------------------------------------------------

class TestInvoice:

    def test_create_invoice(self, db, load_model, project_ids, company_id):
        Invoice = _invoice(load_model)

        inv = Invoice(
            client_name="Metro Development Corp",
            invoice_number="INV-2026-001",
            amount=100000.00,
            tax_amount=10000.00,
            total_amount=110000.00,
            paid_amount=0.0,
            balance_due=110000.00,
            issue_date=date(2026, 3, 1),
            due_date=date(2026, 4, 1),
            project_id=project_ids[0],
            company_id=company_id,
            sequence_name="INV00001",
        )
        db.add(inv)
        db.flush()

        assert inv.id is not None
        assert inv.total_amount == 110000.00
        assert inv.balance_due == 110000.00

    def test_invoice_payment(self, db, load_model, project_ids, company_id):
        Invoice = _invoice(load_model)
        InvoiceStatus = _invoice_status(load_model)

        inv = Invoice(
            client_name="Client A",
            amount=50000,
            tax_amount=5000,
            total_amount=55000,
            paid_amount=0,
            balance_due=55000,
            project_id=project_ids[0],
            company_id=company_id,
            status=InvoiceStatus.SENT,
        )
        db.add(inv)
        db.flush()

        # Record partial payment
        inv.paid_amount = 30000
        inv.balance_due = inv.total_amount - inv.paid_amount
        db.flush()
        assert inv.balance_due == 25000

        # Record full payment
        inv.paid_amount = 55000
        inv.balance_due = 0
        inv.status = InvoiceStatus.PAID
        inv.paid_date = date(2026, 3, 20)
        db.flush()

        assert inv.status == InvoiceStatus.PAID
        assert inv.balance_due == 0
        assert inv.paid_date == date(2026, 3, 20)

    def test_invoice_sequence(self, db, load_model, project_ids, company_id):
        Invoice = _invoice(load_model)

        for i in range(1, 4):
            db.add(Invoice(
                client_name=f"Client {i}",
                project_id=project_ids[0],
                company_id=company_id,
                sequence_name=f"INV{i:05d}",
            ))
        db.flush()

        invs = db.query(Invoice).filter(Invoice.project_id == project_ids[0]).order_by(Invoice.id).all()
        assert invs[0].sequence_name == "INV00001"
        assert invs[2].sequence_name == "INV00003"

    def test_invoice_void(self, db, load_model, project_ids, company_id):
        Invoice = _invoice(load_model)
        InvoiceStatus = _invoice_status(load_model)

        inv = Invoice(client_name="Void test", project_id=project_ids[0], company_id=company_id, status=InvoiceStatus.DRAFT)
        db.add(inv)
        db.flush()

        inv.status = InvoiceStatus.VOID
        db.flush()
        assert inv.status == InvoiceStatus.VOID


# ---------------------------------------------------------------------------
# Bill tests
# ---------------------------------------------------------------------------

class TestBill:

    def test_create_bill(self, db, load_model, project_ids, company_id):
        Bill = _bill(load_model)

        bill = Bill(
            vendor_name="Steel Supply Inc",
            bill_number="BILL-2026-001",
            amount=75000.00,
            tax_amount=7500.00,
            total_amount=82500.00,
            paid_amount=0.0,
            issue_date=date(2026, 3, 5),
            due_date=date(2026, 4, 5),
            project_id=project_ids[0],
            company_id=company_id,
            sequence_name="BILL00001",
        )
        db.add(bill)
        db.flush()

        assert bill.id is not None
        assert bill.total_amount == 82500.00

    def test_bill_payment(self, db, load_model, project_ids, company_id):
        Bill = _bill(load_model)
        BillStatus = _bill_status(load_model)

        bill = Bill(
            vendor_name="Vendor B",
            amount=20000,
            tax_amount=2000,
            total_amount=22000,
            paid_amount=0,
            project_id=project_ids[0],
            company_id=company_id,
            status=BillStatus.APPROVED,
        )
        db.add(bill)
        db.flush()

        bill.paid_amount = 22000
        bill.status = BillStatus.PAID
        bill.paid_date = date(2026, 4, 1)
        db.flush()

        assert bill.status == BillStatus.PAID
        assert bill.paid_amount == 22000

    def test_bill_sequence(self, db, load_model, project_ids, company_id):
        Bill = _bill(load_model)

        for i in range(1, 4):
            db.add(Bill(
                vendor_name=f"Vendor {i}",
                project_id=project_ids[0],
                company_id=company_id,
                sequence_name=f"BILL{i:05d}",
            ))
        db.flush()

        bills = db.query(Bill).filter(Bill.project_id == project_ids[0]).order_by(Bill.id).all()
        assert bills[0].sequence_name == "BILL00001"
        assert bills[2].sequence_name == "BILL00003"

    def test_bill_status_workflow(self, db, load_model, project_ids, company_id):
        Bill = _bill(load_model)
        BillStatus = _bill_status(load_model)

        bill = Bill(vendor_name="Workflow vendor", project_id=project_ids[0], company_id=company_id, status=BillStatus.DRAFT)
        db.add(bill)
        db.flush()

        for st in [BillStatus.RECEIVED, BillStatus.APPROVED, BillStatus.PAID]:
            bill.status = st
            db.flush()
            assert bill.status == st
