"""Finance service - business logic for cost codes, budgets, expenses, invoices, bills"""

import logging
import re
from datetime import date
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from addons.agcm_finance.models.cost_code import CostCode
from addons.agcm_finance.models.budget import Budget
from addons.agcm_finance.models.expense import Expense, ExpenseLine
from addons.agcm_finance.models.invoice import Invoice
from addons.agcm_finance.models.bill import Bill
from addons.agcm_finance.schemas.finance import (
    CostCodeCreate,
    CostCodeUpdate,
    BudgetCreate,
    BudgetUpdate,
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseLineCreate,
    ExpenseLineUpdate,
    InvoiceCreate,
    InvoiceUpdate,
    BillCreate,
    BillUpdate,
    RecordPayment,
)

try:
    from app.core.cache import cache

    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

try:
    from app.models.base import ActivityAction

    ACTIVITY_LOGGING_AVAILABLE = True
except ImportError:
    ACTIVITY_LOGGING_AVAILABLE = False


# Lazy imports to avoid circular dependency issues
def _get_change_order_model():
    from addons.agcm_change_order.models.change_order import ChangeOrder

    return ChangeOrder


logger = logging.getLogger(__name__)

# Sequence configs: (prefix, padding)
SEQUENCES = {
    "expense": ("EXP", 5),
    "invoice": ("INV", 5),
    "bill": ("BILL", 5),
}


def _next_sequence(db: Session, model_class, company_id: int, seq_key: str) -> str:
    prefix, padding = SEQUENCES[seq_key]
    last = (
        db.query(model_class.sequence_name)
        .filter(
            model_class.company_id == company_id, model_class.sequence_name.isnot(None)
        )
        .order_by(model_class.id.desc())
        .first()
    )
    num = 1
    if last and last[0]:
        match = re.search(r"(\d+)$", last[0])
        if match:
            num = int(match.group(1)) + 1
    return f"{prefix}{num:0{padding}d}"


class FinanceService:
    """Handles CRUD for cost codes, budgets, expenses, invoices, and bills."""

    def __init__(self, db: Session, company_id: int, user_id: int):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id

    def _invalidate_finance_cache(self, project_id: int = None):
        """Invalidate finance-related cache."""
        if not CACHE_AVAILABLE:
            return

        if project_id:
            cache.invalidate_pattern_distributed(
                f"agcm_finance:budget_summary:{self.company_id}:{project_id}"
            )
            cache.invalidate_pattern_distributed(
                f"agcm_finance:forecast:{self.company_id}:{project_id}"
            )
        cache.invalidate_pattern_distributed(f"agcm_finance:*")

    # =========================================================================
    # COST CODES
    # =========================================================================

    def list_cost_codes(self, project_id: int) -> List[CostCode]:
        return (
            self.db.query(CostCode)
            .filter(
                CostCode.company_id == self.company_id,
                CostCode.project_id == project_id,
            )
            .order_by(CostCode.code)
            .all()
        )

    def get_cost_code_tree(self, project_id: int) -> list:
        """Build hierarchical tree of cost codes for a project."""
        codes = self.list_cost_codes(project_id)
        code_map = {}
        for c in codes:
            code_map[c.id] = {
                "id": c.id,
                "code": c.code,
                "name": c.name,
                "category": c.category,
                "parent_id": c.parent_id,
                "project_id": c.project_id,
                "company_id": c.company_id,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "children": [],
            }

        roots = []
        for c in codes:
            node = code_map[c.id]
            if c.parent_id and c.parent_id in code_map:
                code_map[c.parent_id]["children"].append(node)
            else:
                roots.append(node)
        return roots

    def get_cost_code(self, cc_id: int) -> Optional[CostCode]:
        return (
            self.db.query(CostCode)
            .filter(CostCode.id == cc_id, CostCode.company_id == self.company_id)
            .first()
        )

    def create_cost_code(self, data: CostCodeCreate) -> CostCode:
        cc = CostCode(
            code=data.code,
            name=data.name,
            category=data.category,
            parent_id=data.parent_id,
            project_id=data.project_id,
            company_id=self.company_id,
        )
        self.db.add(cc)
        self.db.commit()
        self.db.refresh(cc)
        return cc

    def update_cost_code(self, cc_id: int, data: CostCodeUpdate) -> Optional[CostCode]:
        cc = self.get_cost_code(cc_id)
        if not cc:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(cc, key, value)
        self.db.commit()
        self.db.refresh(cc)
        return cc

    def delete_cost_code(self, cc_id: int) -> bool:
        cc = self.get_cost_code(cc_id)
        if not cc:
            return False
        self.db.delete(cc)
        self.db.commit()
        return True

    # =========================================================================
    # BUDGETS
    # =========================================================================

    def list_budgets(self, project_id: int) -> List[Budget]:
        return (
            self.db.query(Budget)
            .filter(
                Budget.company_id == self.company_id,
                Budget.project_id == project_id,
                Budget.is_deleted == False,
            )
            .order_by(Budget.id)
            .all()
        )

    def get_budget_summary(self, project_id: int) -> dict:
        cache_key = f"agcm_finance:budget_summary:{self.company_id}:{project_id}"

        if CACHE_AVAILABLE:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        budgets = self.list_budgets(project_id)
        total_planned = sum(b.planned_amount or 0 for b in budgets)
        total_actual = sum(b.actual_amount or 0 for b in budgets)
        total_committed = sum(b.committed_amount or 0 for b in budgets)
        result = {
            "total_planned": total_planned,
            "total_actual": total_actual,
            "total_committed": total_committed,
            "variance": total_planned - total_actual - total_committed,
            "lines": [
                {
                    "id": b.id,
                    "description": b.description,
                    "planned_amount": b.planned_amount,
                    "actual_amount": b.actual_amount,
                    "committed_amount": b.committed_amount,
                }
                for b in budgets
            ],
        }

        if CACHE_AVAILABLE:
            cache.set(cache_key, result, ttl=300)

        return result

    def get_budget(self, budget_id: int) -> Optional[Budget]:
        return (
            self.db.query(Budget)
            .filter(
                Budget.id == budget_id,
                Budget.company_id == self.company_id,
                Budget.is_deleted == False,
            )
            .first()
        )

    def create_budget(self, data: BudgetCreate) -> Budget:
        budget = Budget(
            project_id=data.project_id,
            cost_code_id=data.cost_code_id,
            description=data.description,
            planned_amount=data.planned_amount or 0,
            actual_amount=data.actual_amount or 0,
            committed_amount=data.committed_amount or 0,
            company_id=self.company_id,
            created_by=self.user_id,
        )
        self.db.add(budget)
        self.db.commit()
        self.db.refresh(budget)

        self._invalidate_finance_cache(data.project_id)

        if ACTIVITY_LOGGING_AVAILABLE:
            budget.log_activity(
                self.db,
                ActivityAction.CREATE,
                user_id=self.user_id,
                description=f"Budget line '{budget.description}' created",
            )

        return budget

    def update_budget(self, budget_id: int, data: BudgetUpdate) -> Optional[Budget]:
        budget = self.get_budget(budget_id)
        if not budget:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(budget, key, value)
        budget.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(budget)

        self._invalidate_finance_cache(budget.project_id)

        if ACTIVITY_LOGGING_AVAILABLE:
            budget.log_activity(
                self.db,
                ActivityAction.UPDATE,
                user_id=self.user_id,
                description=f"Budget line '{budget.description}' updated",
            )

        return budget

    def delete_budget(self, budget_id: int) -> bool:
        budget = self.get_budget(budget_id)
        if not budget:
            return False
        project_id = budget.project_id
        description = budget.description
        budget.soft_delete(user_id=self.user_id)
        self.db.commit()

        self._invalidate_finance_cache(project_id)

        if ACTIVITY_LOGGING_AVAILABLE:
            budget.log_activity(
                self.db,
                ActivityAction.ARCHIVE,
                user_id=self.user_id,
                description=f"Budget line '{description}' archived",
            )

        return True

    # =========================================================================
    # EXPENSES
    # =========================================================================

    def list_expenses(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        page_size = min(page_size, 200)
        query = self.db.query(Expense).filter(
            Expense.company_id == self.company_id,
            Expense.is_deleted == False,
        )

        if project_id:
            query = query.filter(Expense.project_id == project_id)
        if status:
            query = query.filter(Expense.status == status)

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(Expense.id.desc()).offset(skip).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_expense(self, expense_id: int) -> Optional[Expense]:
        return (
            self.db.query(Expense)
            .filter(
                Expense.id == expense_id,
                Expense.company_id == self.company_id,
                Expense.is_deleted == False,
            )
            .first()
        )

    def get_expense_detail(self, expense_id: int) -> Optional[dict]:
        exp = self.get_expense(expense_id)
        if not exp:
            return None

        lines = (
            self.db.query(ExpenseLine)
            .filter(ExpenseLine.expense_id == expense_id)
            .order_by(ExpenseLine.id)
            .all()
        )

        line_dicts = [
            {
                "id": l.id,
                "expense_id": l.expense_id,
                "description": l.description,
                "quantity": l.quantity,
                "unit": l.unit,
                "unit_cost": l.unit_cost,
                "total_cost": l.total_cost,
                "cost_code_id": l.cost_code_id,
                "category": l.category,
                "company_id": l.company_id,
                "created_at": l.created_at,
                "updated_at": l.updated_at,
            }
            for l in lines
        ]

        result = {}
        for c in exp.__table__.columns:
            val = getattr(exp, c.key, None)
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            result[c.key] = val

        return {
            **result,
            "lines": line_dicts,
        }

    def create_expense(self, data: ExpenseCreate) -> Expense:
        exp = Expense(
            company_id=self.company_id,
            sequence_name=_next_sequence(self.db, Expense, self.company_id, "expense"),
            description=data.description,
            vendor=data.vendor,
            status="draft",
            project_id=data.project_id,
            created_by=self.user_id,
        )
        self.db.add(exp)
        self.db.flush()

        if data.lines:
            for line_data in data.lines:
                line = ExpenseLine(
                    expense_id=exp.id,
                    description=line_data.description,
                    quantity=line_data.quantity or 1.0,
                    unit=line_data.unit,
                    unit_cost=line_data.unit_cost or 0.0,
                    total_cost=line_data.total_cost or 0.0,
                    cost_code_id=line_data.cost_code_id,
                    category=line_data.category,
                    company_id=self.company_id,
                )
                self.db.add(line)

        self.db.commit()
        self.db.refresh(exp)

        self._invalidate_finance_cache(data.project_id)

        if ACTIVITY_LOGGING_AVAILABLE:
            exp.log_activity(
                self.db,
                ActivityAction.CREATE,
                user_id=self.user_id,
                description=f"Expense '{exp.description}' created",
            )

        return exp

    def update_expense(self, expense_id: int, data: ExpenseUpdate) -> Optional[Expense]:
        exp = self.get_expense(expense_id)
        if not exp:
            return None

        update_data = data.model_dump(exclude_unset=True)
        lines_data = update_data.pop("lines", None)

        for key, value in update_data.items():
            setattr(exp, key, value)
        exp.updated_by = self.user_id

        if lines_data is not None:
            self.db.query(ExpenseLine).filter(
                ExpenseLine.expense_id == expense_id
            ).delete()
            for line_data in lines_data:
                line = ExpenseLine(
                    expense_id=expense_id,
                    description=line_data.get("description", ""),
                    quantity=line_data.get("quantity", 1.0),
                    unit=line_data.get("unit"),
                    unit_cost=line_data.get("unit_cost", 0.0),
                    total_cost=line_data.get("total_cost", 0.0),
                    cost_code_id=line_data.get("cost_code_id"),
                    category=line_data.get("category"),
                    company_id=self.company_id,
                )
                self.db.add(line)

        self.db.commit()
        self.db.refresh(exp)

        self._invalidate_finance_cache(exp.project_id)

        if ACTIVITY_LOGGING_AVAILABLE:
            exp.log_activity(
                self.db,
                ActivityAction.UPDATE,
                user_id=self.user_id,
                description=f"Expense '{exp.description}' updated",
            )

        return exp

    def delete_expense(self, expense_id: int) -> bool:
        exp = self.get_expense(expense_id)
        if not exp:
            return False
        project_id = exp.project_id
        description = exp.description
        exp.soft_delete(user_id=self.user_id)
        self.db.commit()

        self._invalidate_finance_cache(project_id)

        if ACTIVITY_LOGGING_AVAILABLE:
            exp.log_activity(
                self.db,
                ActivityAction.ARCHIVE,
                user_id=self.user_id,
                description=f"Expense '{description}' archived",
            )

        return True

    def approve_expense(self, expense_id: int) -> Optional[Expense]:
        exp = self.get_expense(expense_id)
        if not exp:
            return None
        exp.status = ExpenseStatus.APPROVED.value
        exp.updated_by = self.user_id

        # Post actual cost to budget from expense lines
        try:
            from addons.agcm.services.budget_posting import post_to_budget
            total = sum(
                (line.total_cost or 0) for line in (exp.lines or [])
            )
            if exp.project_id and total:
                post_to_budget(
                    self.db, exp.project_id, self.company_id,
                    "actual_amount", total,
                    description="Expenses",
                )
        except ImportError:
            pass

        self.db.commit()
        self.db.refresh(exp)
        self._invalidate_finance_cache(exp.project_id)
        return exp

    # --- Expense Line standalone CRUD ---

    def add_expense_line(
        self, data: ExpenseLineCreate, expense_id: int
    ) -> Optional[ExpenseLine]:
        exp = self.get_expense(expense_id)
        if not exp:
            return None
        line = ExpenseLine(
            expense_id=expense_id,
            description=data.description,
            quantity=data.quantity or 1.0,
            unit=data.unit,
            unit_cost=data.unit_cost or 0.0,
            total_cost=data.total_cost or 0.0,
            cost_code_id=data.cost_code_id,
            category=data.category,
            company_id=self.company_id,
        )
        self.db.add(line)
        self.db.commit()
        self.db.refresh(line)
        return line

    def update_expense_line(
        self, line_id: int, data: ExpenseLineUpdate
    ) -> Optional[ExpenseLine]:
        line = (
            self.db.query(ExpenseLine)
            .filter(
                ExpenseLine.id == line_id, ExpenseLine.company_id == self.company_id
            )
            .first()
        )
        if not line:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(line, key, value)
        self.db.commit()
        self.db.refresh(line)
        return line

    def delete_expense_line(self, line_id: int) -> bool:
        line = (
            self.db.query(ExpenseLine)
            .filter(
                ExpenseLine.id == line_id, ExpenseLine.company_id == self.company_id
            )
            .first()
        )
        if not line:
            return False
        self.db.delete(line)
        self.db.commit()
        return True

    # =========================================================================
    # INVOICES
    # =========================================================================

    def list_invoices(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        page_size = min(page_size, 200)
        query = self.db.query(Invoice).filter(
            Invoice.company_id == self.company_id,
            Invoice.is_deleted == False,
        )

        if project_id:
            query = query.filter(Invoice.project_id == project_id)
        if status:
            query = query.filter(Invoice.status == status)

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(Invoice.id.desc()).offset(skip).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_invoice(self, invoice_id: int) -> Optional[Invoice]:
        return (
            self.db.query(Invoice)
            .filter(
                Invoice.id == invoice_id,
                Invoice.company_id == self.company_id,
                Invoice.is_deleted == False,
            )
            .first()
        )

    def create_invoice(self, data: InvoiceCreate) -> Invoice:
        total = (data.amount or 0) + (data.tax_amount or 0)
        inv = Invoice(
            company_id=self.company_id,
            sequence_name=_next_sequence(self.db, Invoice, self.company_id, "invoice"),
            invoice_number=data.invoice_number,
            client_name=data.client_name,
            status="draft",
            amount=data.amount or 0,
            tax_amount=data.tax_amount or 0,
            total_amount=data.total_amount or total,
            paid_amount=0,
            balance_due=data.total_amount or total,
            issue_date=data.issue_date,
            due_date=data.due_date,
            project_id=data.project_id,
            created_by=self.user_id,
        )
        self.db.add(inv)
        self.db.commit()
        self.db.refresh(inv)

        self._invalidate_finance_cache(data.project_id)

        if ACTIVITY_LOGGING_AVAILABLE:
            inv.log_activity(
                self.db,
                ActivityAction.CREATE,
                user_id=self.user_id,
                description=f"Invoice {inv.sequence_name} created for {inv.client_name}",
            )

        return inv

    def update_invoice(self, invoice_id: int, data: InvoiceUpdate) -> Optional[Invoice]:
        inv = self.get_invoice(invoice_id)
        if not inv:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(inv, key, value)

        inv.balance_due = (inv.total_amount or 0) - (inv.paid_amount or 0)
        inv.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(inv)

        self._invalidate_finance_cache(inv.project_id)

        if ACTIVITY_LOGGING_AVAILABLE:
            inv.log_activity(
                self.db,
                ActivityAction.UPDATE,
                user_id=self.user_id,
                description=f"Invoice {inv.sequence_name} updated",
            )

        return inv

    def delete_invoice(self, invoice_id: int) -> bool:
        inv = self.get_invoice(invoice_id)
        if not inv:
            return False
        project_id = inv.project_id
        sequence = inv.sequence_name
        inv.soft_delete(user_id=self.user_id)
        self.db.commit()

        self._invalidate_finance_cache(project_id)

        if ACTIVITY_LOGGING_AVAILABLE:
            inv.log_activity(
                self.db,
                ActivityAction.ARCHIVE,
                user_id=self.user_id,
                description=f"Invoice {sequence} archived",
            )

        return True

    def record_invoice_payment(
        self, invoice_id: int, payment: RecordPayment
    ) -> Optional[Invoice]:
        inv = self.get_invoice(invoice_id)
        if not inv:
            return None

        inv.paid_amount = (inv.paid_amount or 0) + payment.amount
        inv.balance_due = (inv.total_amount or 0) - inv.paid_amount

        if inv.balance_due <= 0:
            inv.balance_due = 0
            inv.status = "paid"
            inv.paid_date = date.today()

        inv.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(inv)

        self._invalidate_finance_cache(inv.project_id)

        if ACTIVITY_LOGGING_AVAILABLE:
            inv.log_activity(
                self.db,
                ActivityAction.UPDATE,
                user_id=self.user_id,
                description=f"Payment of {payment.amount} recorded for invoice {inv.sequence_name}",
            )

        return inv

    # =========================================================================
    # BILLS
    # =========================================================================

    def list_bills(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        page_size = min(page_size, 200)
        query = self.db.query(Bill).filter(
            Bill.company_id == self.company_id,
            Bill.is_deleted == False,
        )

        if project_id:
            query = query.filter(Bill.project_id == project_id)
        if status:
            query = query.filter(Bill.status == status)

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(Bill.id.desc()).offset(skip).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_bill(self, bill_id: int) -> Optional[Bill]:
        return (
            self.db.query(Bill)
            .filter(
                Bill.id == bill_id,
                Bill.company_id == self.company_id,
                Bill.is_deleted == False,
            )
            .first()
        )

    def create_bill(self, data: BillCreate) -> Bill:
        total = (data.amount or 0) + (data.tax_amount or 0)
        bill = Bill(
            company_id=self.company_id,
            sequence_name=_next_sequence(self.db, Bill, self.company_id, "bill"),
            bill_number=data.bill_number,
            vendor_name=data.vendor_name,
            status="draft",
            amount=data.amount or 0,
            tax_amount=data.tax_amount or 0,
            total_amount=data.total_amount or total,
            paid_amount=0,
            issue_date=data.issue_date,
            due_date=data.due_date,
            project_id=data.project_id,
            created_by=self.user_id,
        )
        self.db.add(bill)
        self.db.commit()
        self.db.refresh(bill)

        self._invalidate_finance_cache(data.project_id)

        if ACTIVITY_LOGGING_AVAILABLE:
            bill.log_activity(
                self.db,
                ActivityAction.CREATE,
                user_id=self.user_id,
                description=f"Bill {bill.sequence_name} created for {bill.vendor_name}",
            )

        return bill

    def update_bill(self, bill_id: int, data: BillUpdate) -> Optional[Bill]:
        bill = self.get_bill(bill_id)
        if not bill:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(bill, key, value)
        bill.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(bill)

        self._invalidate_finance_cache(bill.project_id)

        if ACTIVITY_LOGGING_AVAILABLE:
            bill.log_activity(
                self.db,
                ActivityAction.UPDATE,
                user_id=self.user_id,
                description=f"Bill {bill.sequence_name} updated",
            )

        return bill

    def delete_bill(self, bill_id: int) -> bool:
        bill = self.get_bill(bill_id)
        if not bill:
            return False
        project_id = bill.project_id
        sequence = bill.sequence_name
        bill.soft_delete(user_id=self.user_id)
        self.db.commit()

        self._invalidate_finance_cache(project_id)

        if ACTIVITY_LOGGING_AVAILABLE:
            bill.log_activity(
                self.db,
                ActivityAction.ARCHIVE,
                user_id=self.user_id,
                description=f"Bill {sequence} archived",
            )

        return True

    def record_bill_payment(
        self, bill_id: int, payment: RecordPayment
    ) -> Optional[Bill]:
        bill = self.get_bill(bill_id)
        if not bill:
            return None

        bill.paid_amount = (bill.paid_amount or 0) + payment.amount
        remaining = (bill.total_amount or 0) - bill.paid_amount

        if remaining <= 0:
            bill.status = "paid"
            bill.paid_date = date.today()

        bill.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(bill)

        self._invalidate_finance_cache(bill.project_id)

        if ACTIVITY_LOGGING_AVAILABLE:
            bill.log_activity(
                self.db,
                ActivityAction.UPDATE,
                user_id=self.user_id,
                description=f"Payment of {payment.amount} recorded for bill {bill.sequence_name}",
            )

        return bill

    # =========================================================================
    # BUDGET FORECASTING (EAC/ETC)
    # =========================================================================

    def get_budget_forecast(self, project_id: int) -> dict:
        """Compute Estimate at Completion / Estimate to Complete forecast."""
        budgets = self.list_budgets(project_id)

        original_budget = sum(b.planned_amount or 0 for b in budgets)
        committed = sum(b.committed_amount or 0 for b in budgets)
        actual_spent = sum(b.actual_amount or 0 for b in budgets)

        # Get approved change order cost impacts
        approved_changes = 0.0
        try:
            ChangeOrder = _get_change_order_model()
            cos = (
                self.db.query(func.coalesce(func.sum(ChangeOrder.cost_impact), 0))
                .filter(
                    ChangeOrder.project_id == project_id,
                    ChangeOrder.company_id == self.company_id,
                    ChangeOrder.status == "approved",
                )
                .scalar()
            )
            approved_changes = float(cos or 0)
        except Exception:
            pass

        revised_budget = original_budget + approved_changes

        # Trend factor: ratio of committed-but-unspent work
        if committed > 0 and actual_spent > 0:
            trend_factor = actual_spent / committed if committed else 1.0
        else:
            trend_factor = 1.0

        remaining_committed = max(committed - actual_spent, 0)
        estimated_at_completion = actual_spent + remaining_committed * trend_factor
        # Ensure EAC is at least the revised budget when there is no variance signal
        if estimated_at_completion < revised_budget and actual_spent == 0:
            estimated_at_completion = revised_budget

        estimate_to_complete = max(estimated_at_completion - actual_spent, 0)
        variance = revised_budget - estimated_at_completion
        pct_complete = (actual_spent / revised_budget * 100) if revised_budget else 0
        cpi = (
            (revised_budget / estimated_at_completion) if estimated_at_completion else 0
        )

        # Build per-cost-code breakdown
        by_cost_code = []
        for b in budgets:
            cc_forecast = (b.actual_amount or 0) + max(
                (b.committed_amount or 0) - (b.actual_amount or 0), 0
            ) * trend_factor
            by_cost_code.append(
                {
                    "budget_id": b.id,
                    "cost_code_id": b.cost_code_id,
                    "description": b.description,
                    "planned": b.planned_amount or 0,
                    "committed": b.committed_amount or 0,
                    "actual": b.actual_amount or 0,
                    "forecast": round(cc_forecast, 2),
                }
            )

        return {
            "original_budget": round(original_budget, 2),
            "approved_changes": round(approved_changes, 2),
            "revised_budget": round(revised_budget, 2),
            "committed": round(committed, 2),
            "actual_spent": round(actual_spent, 2),
            "estimated_at_completion": round(estimated_at_completion, 2),
            "estimate_to_complete": round(estimate_to_complete, 2),
            "variance": round(variance, 2),
            "pct_complete": round(pct_complete, 2),
            "cost_performance_index": round(cpi, 4),
            "by_cost_code": by_cost_code,
        }
