"""
AGCM Budget Posting — shared helper for posting costs to project budgets.

Provides a standard upsert pattern for incrementing budget amounts when
entities are approved (committed) or paid (actual).

Usage:
    from addons.agcm.services.budget_posting import post_to_budget, reverse_budget_posting

    # PO approved → increment committed
    post_to_budget(db, project_id, company_id, "committed_amount", po.total_amount,
                   description="Purchase Orders")

    # Vendor bill approved → increment actual
    post_to_budget(db, project_id, company_id, "actual_amount", bill.total_amount,
                   description="Vendor Bills")

    # Timesheet approved → increment actual
    post_to_budget(db, project_id, company_id, "actual_amount", ts.total_cost,
                   description="Labor (Timesheets)")
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

VALID_COLUMNS = ("committed_amount", "actual_amount", "planned_amount")


def _get_budget_model():
    """Lazy-import Budget model (works in both runtime and tests)."""
    import sys
    mod = sys.modules.get("agcm_finance_budget")
    if mod:
        return mod.Budget
    from addons.agcm_finance.models.budget import Budget
    return Budget


def post_to_budget(
    db: Session,
    project_id: int,
    company_id: int,
    column: str,
    amount: float,
    cost_code_id: Optional[int] = None,
    description: str = "",
) -> bool:
    """
    Increment a budget column for a project.

    Upserts a budget line matching (project_id, company_id, description).
    If no matching line exists, creates one.

    Args:
        db: Database session
        project_id: Project to post to
        company_id: Company scope
        column: "committed_amount" or "actual_amount"
        amount: Amount to add (positive = increase, negative = decrease)
        cost_code_id: Optional cost code FK
        description: Budget line description for matching (e.g. "Purchase Orders")

    Returns:
        True if posted successfully, False on error.
    """
    if column not in VALID_COLUMNS:
        logger.error("Invalid budget column: %s", column)
        return False

    if not amount or not project_id:
        return False

    try:
        Budget = _get_budget_model()

        budget_line = (
            db.query(Budget)
            .filter(
                Budget.project_id == project_id,
                Budget.company_id == company_id,
                Budget.description == description,
            )
            .first()
        )

        if budget_line:
            current = getattr(budget_line, column) or 0
            setattr(budget_line, column, current + amount)
        else:
            kwargs = {
                "project_id": project_id,
                "cost_code_id": cost_code_id,
                "description": description,
                "planned_amount": 0,
                "actual_amount": 0,
                "committed_amount": 0,
                "company_id": company_id,
            }
            kwargs[column] = amount
            budget_line = Budget(**kwargs)
            db.add(budget_line)

        logger.info(
            "Budget posted: %s +%.2f to %s for project %d (%s)",
            column, amount, description, project_id, "updated" if budget_line.id else "created",
        )
        return True

    except ImportError:
        logger.debug("agcm_finance not installed — skipping budget posting")
        return False
    except Exception as e:
        logger.warning("Budget posting failed: %s", e)
        return False


def reverse_budget_posting(
    db: Session,
    project_id: int,
    company_id: int,
    column: str,
    amount: float,
    description: str = "",
) -> bool:
    """
    Reverse a previous budget posting (e.g., when an entity is voided/rejected
    after approval).

    Decrements the specified column by the given amount.
    """
    return post_to_budget(
        db=db,
        project_id=project_id,
        company_id=company_id,
        column=column,
        amount=-amount,
        description=description,
    )
