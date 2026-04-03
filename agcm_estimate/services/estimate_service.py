"""Estimate service — business logic for construction estimating."""

import logging
import re
from datetime import date
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from addons.agcm_estimate.models.cost_catalog import CostCatalog, CostItem
from addons.agcm_estimate.models.assembly import Assembly, AssemblyItem
from addons.agcm_estimate.models.estimate import (
    Estimate,
    EstimateGroup,
    EstimateLineItem,
    EstimateStatus,
)
from addons.agcm_estimate.models.estimate_markup import EstimateMarkup, MarkupType
from addons.agcm_estimate.models.proposal import Proposal, ProposalStatus
from addons.agcm_estimate.models.takeoff import TakeoffSheet, TakeoffMeasurement

from addons.agcm_estimate.schemas.estimate import (
    CostCatalogCreate,
    CostCatalogUpdate,
    CostItemCreate,
    CostItemUpdate,
    AssemblyCreate,
    AssemblyUpdate,
    AssemblyItemCreate,
    AssemblyItemUpdate,
    EstimateCreate,
    EstimateUpdate,
    EstimateGroupCreate,
    EstimateGroupUpdate,
    EstimateLineItemCreate,
    EstimateLineItemUpdate,
    EstimateLineItemResponse,
    EstimateMarkupCreate,
    EstimateMarkupUpdate,
    ProposalCreate,
    ProposalUpdate,
    TakeoffSheetCreate,
    TakeoffSheetUpdate,
    TakeoffMeasurementCreate,
    TakeoffMeasurementUpdate,
    EstimateSummary,
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

logger = logging.getLogger(__name__)


class EstimateService:
    """Business logic for construction estimating, takeoff, and proposals."""

    def __init__(self, db: Session, company_id: int, user_id: int):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id

    def _invalidate_estimate_cache(
        self, estimate_id: int = None, project_id: int = None
    ):
        """Invalidate estimate-related cache."""
        if not CACHE_AVAILABLE:
            return

        if estimate_id:
            cache.invalidate(f"agcm_estimate:detail:{self.company_id}:{estimate_id}")
        if project_id:
            cache.invalidate_pattern_distributed(
                f"agcm_estimate:project:{self.company_id}:{project_id}:*"
            )
        cache.invalidate_pattern_distributed(f"agcm_estimate:*")

    # =========================================================================
    # SEQUENCE GENERATION
    # =========================================================================

    def _next_sequence(self, model_class, prefix: str, padding: int = 5) -> str:
        """Generate next sequence: EST00001, PROP00001, TO00001."""
        last = (
            self.db.query(model_class.sequence_name)
            .filter(model_class.company_id == self.company_id)
            .filter(model_class.sequence_name.isnot(None))
            .order_by(model_class.id.desc())
            .first()
        )
        num = 1
        if last and last[0]:
            match = re.search(r"(\d+)$", last[0])
            if match:
                num = int(match.group(1)) + 1
        return f"{prefix}{num:0{padding}d}"

    # =========================================================================
    # COST CATALOG CRUD
    # =========================================================================

    def list_catalogs(self, page: int = 1, page_size: int = 20) -> dict:
        query = self.db.query(CostCatalog).filter(
            CostCatalog.company_id == self.company_id
        )
        total = query.count()
        items = (
            query.order_by(CostCatalog.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def create_catalog(self, data: CostCatalogCreate) -> CostCatalog:
        catalog = CostCatalog(
            company_id=self.company_id,
            name=data.name,
            description=data.description,
            is_default=data.is_default,
            created_by=self.user_id,
        )
        if data.is_default:
            # Unset any existing default
            self.db.query(CostCatalog).filter(
                CostCatalog.company_id == self.company_id,
                CostCatalog.is_default == True,
            ).update({"is_default": False})
        self.db.add(catalog)
        self.db.commit()
        self.db.refresh(catalog)
        return catalog

    def update_catalog(
        self, catalog_id: int, data: CostCatalogUpdate
    ) -> Optional[CostCatalog]:
        catalog = (
            self.db.query(CostCatalog)
            .filter(
                CostCatalog.id == catalog_id,
                CostCatalog.company_id == self.company_id,
            )
            .first()
        )
        if not catalog:
            return None
        update_data = data.model_dump(exclude_unset=True)
        if update_data.get("is_default"):
            self.db.query(CostCatalog).filter(
                CostCatalog.company_id == self.company_id,
                CostCatalog.is_default == True,
                CostCatalog.id != catalog_id,
            ).update({"is_default": False})
        for key, value in update_data.items():
            setattr(catalog, key, value)
        catalog.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(catalog)
        return catalog

    def delete_catalog(self, catalog_id: int) -> bool:
        catalog = (
            self.db.query(CostCatalog)
            .filter(
                CostCatalog.id == catalog_id,
                CostCatalog.company_id == self.company_id,
            )
            .first()
        )
        if not catalog:
            return False
        self.db.delete(catalog)
        self.db.commit()
        return True

    # =========================================================================
    # COST ITEM CRUD
    # =========================================================================

    def list_cost_items(
        self,
        catalog_id: Optional[int] = None,
        item_type: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        query = self.db.query(CostItem).filter(CostItem.company_id == self.company_id)
        if catalog_id:
            query = query.filter(CostItem.catalog_id == catalog_id)
        if item_type:
            query = query.filter(CostItem.item_type == item_type)
        if search:
            term = f"%{search}%"
            query = query.filter(
                (CostItem.name.ilike(term))
                | (CostItem.cost_code.ilike(term))
                | (CostItem.vendor.ilike(term))
            )
        total = query.count()
        items = (
            query.order_by(CostItem.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def create_cost_item(self, data: CostItemCreate) -> CostItem:
        item = CostItem(
            company_id=self.company_id,
            catalog_id=data.catalog_id,
            name=data.name,
            description=data.description,
            item_type=data.item_type,
            unit=data.unit,
            unit_cost=data.unit_cost,
            unit_price=data.unit_price,
            taxable=data.taxable,
            cost_code=data.cost_code,
            vendor=data.vendor,
            category=data.category,
            is_active=data.is_active,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_cost_item(
        self, item_id: int, data: CostItemUpdate
    ) -> Optional[CostItem]:
        item = (
            self.db.query(CostItem)
            .filter(
                CostItem.id == item_id,
                CostItem.company_id == self.company_id,
            )
            .first()
        )
        if not item:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(item, key, value)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_cost_item(self, item_id: int) -> bool:
        item = (
            self.db.query(CostItem)
            .filter(
                CostItem.id == item_id,
                CostItem.company_id == self.company_id,
            )
            .first()
        )
        if not item:
            return False
        self.db.delete(item)
        self.db.commit()
        return True

    # =========================================================================
    # ASSEMBLY CRUD
    # =========================================================================

    def list_assemblies(
        self, category: Optional[str] = None, page: int = 1, page_size: int = 20
    ) -> dict:
        query = self.db.query(Assembly).filter(Assembly.company_id == self.company_id)
        if category:
            query = query.filter(Assembly.category == category)
        total = query.count()
        items = (
            query.order_by(Assembly.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_assembly(self, assembly_id: int) -> Optional[Assembly]:
        return (
            self.db.query(Assembly)
            .filter(
                Assembly.id == assembly_id,
                Assembly.company_id == self.company_id,
            )
            .first()
        )

    def create_assembly(self, data: AssemblyCreate) -> Assembly:
        assembly = Assembly(
            company_id=self.company_id,
            name=data.name,
            description=data.description,
            category=data.category,
            is_active=data.is_active,
            created_by=self.user_id,
        )
        self.db.add(assembly)
        self.db.flush()

        for item_data in data.items or []:
            ai = AssemblyItem(
                assembly_id=assembly.id,
                company_id=self.company_id,
                cost_item_id=item_data.cost_item_id,
                name=item_data.name,
                description=item_data.description,
                item_type=item_data.item_type,
                quantity=item_data.quantity,
                unit=item_data.unit,
                unit_cost=item_data.unit_cost,
                waste_factor=item_data.waste_factor,
            )
            self.db.add(ai)

        self.db.commit()
        self.db.refresh(assembly)
        return assembly

    def update_assembly(
        self, assembly_id: int, data: AssemblyUpdate
    ) -> Optional[Assembly]:
        assembly = self.get_assembly(assembly_id)
        if not assembly:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(assembly, key, value)
        assembly.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(assembly)
        return assembly

    def delete_assembly(self, assembly_id: int) -> bool:
        assembly = self.get_assembly(assembly_id)
        if not assembly:
            return False
        self.db.delete(assembly)
        self.db.commit()
        return True

    def create_assembly_item(
        self, data: AssemblyItemCreate, assembly_id: int
    ) -> AssemblyItem:
        # Verify assembly belongs to this company (IDOR protection)
        assembly = self.get_assembly(assembly_id)
        if not assembly:
            raise ValueError("Assembly not found or access denied")
        item = AssemblyItem(
            assembly_id=assembly_id,
            company_id=self.company_id,
            cost_item_id=data.cost_item_id,
            name=data.name,
            description=data.description,
            item_type=data.item_type,
            quantity=data.quantity,
            unit=data.unit,
            unit_cost=data.unit_cost,
            waste_factor=data.waste_factor,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_assembly_item(
        self, item_id: int, data: AssemblyItemUpdate
    ) -> Optional[AssemblyItem]:
        item = (
            self.db.query(AssemblyItem)
            .filter(
                AssemblyItem.id == item_id,
                AssemblyItem.company_id == self.company_id,
            )
            .first()
        )
        if not item:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(item, key, value)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_assembly_item(self, item_id: int) -> bool:
        item = (
            self.db.query(AssemblyItem)
            .filter(
                AssemblyItem.id == item_id,
                AssemblyItem.company_id == self.company_id,
            )
            .first()
        )
        if not item:
            return False
        self.db.delete(item)
        self.db.commit()
        return True

    # =========================================================================
    # ESTIMATE CRUD
    # =========================================================================

    def list_estimates(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        query = self.db.query(Estimate).filter(Estimate.company_id == self.company_id)
        if project_id:
            query = query.filter(Estimate.project_id == project_id)
        if status:
            query = query.filter(Estimate.status == status)
        total = query.count()
        items = (
            query.order_by(Estimate.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_estimate(self, estimate_id: int) -> Optional[Estimate]:
        return (
            self.db.query(Estimate)
            .filter(
                Estimate.id == estimate_id,
                Estimate.company_id == self.company_id,
            )
            .first()
        )

    def get_estimate_detail(self, estimate_id: int) -> Optional[dict]:
        """Full detail with groups, line items, markups, and summary."""
        estimate = self.get_estimate(estimate_id)
        if not estimate:
            return None

        # Count line items from already-loaded relationships (no extra query)
        line_item_count = sum(len(g.line_items) for g in estimate.groups)

        groups_data = []
        for group in estimate.groups:
            li_list = []
            for li in group.line_items:
                li_list.append(
                    {c.key: getattr(li, c.key) for c in li.__table__.columns}
                )
            groups_data.append(
                {
                    **{c.key: getattr(group, c.key) for c in group.__table__.columns},
                    "line_items": li_list,
                }
            )

        markups_data = []
        for m in estimate.markups:
            markups_data.append({c.key: getattr(m, c.key) for c in m.__table__.columns})

        summary = {
            "subtotal": estimate.subtotal or 0,
            "markup_total": estimate.markup_total or 0,
            "tax_total": estimate.tax_total or 0,
            "grand_total": estimate.grand_total or 0,
            "line_item_count": line_item_count,
            "group_count": len(estimate.groups),
        }

        return {
            **{c.key: getattr(estimate, c.key) for c in estimate.__table__.columns},
            "groups": groups_data,
            "markups": markups_data,
            "summary": summary,
        }

    def create_estimate(self, data: EstimateCreate) -> Estimate:
        estimate = Estimate(
            company_id=self.company_id,
            sequence_name=self._next_sequence(Estimate, "EST"),
            project_id=data.project_id,
            name=data.name,
            description=data.description,
            estimate_type=data.estimate_type,
            tax_rate=data.tax_rate,
            notes=data.notes,
            created_by=self.user_id,
        )
        self.db.add(estimate)
        self.db.commit()
        self.db.refresh(estimate)
        return estimate

    def update_estimate(
        self, estimate_id: int, data: EstimateUpdate
    ) -> Optional[Estimate]:
        estimate = self.get_estimate(estimate_id)
        if not estimate:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(estimate, key, value)
        estimate.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(estimate)
        return estimate

    def delete_estimate(self, estimate_id: int) -> bool:
        estimate = self.get_estimate(estimate_id)
        if not estimate:
            return False
        self.db.delete(estimate)
        self.db.commit()
        return True

    # =========================================================================
    # RECALCULATE ESTIMATE
    # =========================================================================

    def recalculate_estimate(self, estimate_id: int) -> Optional[Estimate]:
        """Recalculate all totals from line items, markups, and tax."""
        estimate = self.get_estimate(estimate_id)
        if not estimate:
            return None

        # 1. Recalculate each line item using already-loaded relationships
        subtotal_cost = 0.0
        subtotal_price = 0.0
        tax_base = 0.0

        for group in estimate.groups:
            group_total = 0.0
            for li in group.line_items:
                li.total_cost = li.quantity * li.unit_cost
                li.unit_price = li.unit_cost * (1 + (li.markup_pct or 0) / 100)
                li.total_price = li.quantity * li.unit_price
                subtotal_cost += li.total_cost
                subtotal_price += li.total_price
                group_total += li.total_cost
                if li.taxable:
                    tax_base += li.total_price
            # 2. Update group subtotals
            group.subtotal = group_total

        # 3. Calculate markups (already loaded via selectin relationship)
        markups = sorted(estimate.markups, key=lambda m: m.display_order or 0)

        markup_total = 0.0
        running_base = subtotal_price

        for markup in markups:
            if (
                markup.markup_type == MarkupType.PERCENTAGE.value
                or markup.markup_type == MarkupType.PERCENTAGE
            ):
                if markup.is_compounding:
                    markup.calculated_amount = running_base * (markup.value / 100)
                else:
                    markup.calculated_amount = subtotal_price * (markup.value / 100)
            else:
                # lump_sum
                markup.calculated_amount = markup.value

            markup_total += markup.calculated_amount
            if markup.is_compounding:
                running_base += markup.calculated_amount

        # 4. Calculate tax
        tax_rate = estimate.tax_rate or 0
        tax_total = tax_base * (tax_rate / 100)

        # 5. Update estimate totals
        estimate.subtotal = subtotal_cost
        estimate.markup_total = markup_total
        estimate.tax_total = tax_total
        estimate.grand_total = subtotal_price + markup_total + tax_total

        self.db.commit()
        self.db.refresh(estimate)
        return estimate

    # =========================================================================
    # CREATE VERSION
    # =========================================================================

    def create_version(self, estimate_id: int) -> Optional[Estimate]:
        """Snapshot current estimate and create a new version."""
        original = self.get_estimate(estimate_id)
        if not original:
            return None

        # Mark original as superseded
        original.status = EstimateStatus.SUPERSEDED.value

        # Create new version
        new_est = Estimate(
            company_id=self.company_id,
            sequence_name=self._next_sequence(Estimate, "EST"),
            project_id=original.project_id,
            name=original.name,
            description=original.description,
            version=original.version + 1,
            status=EstimateStatus.DRAFT.value,
            estimate_type=original.estimate_type,
            tax_rate=original.tax_rate,
            notes=original.notes,
            parent_estimate_id=original.id,
            created_by=self.user_id,
        )
        self.db.add(new_est)
        self.db.flush()

        # Copy groups and line items
        for group in original.groups:
            new_group = EstimateGroup(
                estimate_id=new_est.id,
                company_id=self.company_id,
                name=group.name,
                description=group.description,
                display_order=group.display_order,
            )
            self.db.add(new_group)
            self.db.flush()

            for li in group.line_items:
                new_li = EstimateLineItem(
                    group_id=new_group.id,
                    estimate_id=new_est.id,
                    company_id=self.company_id,
                    cost_item_id=li.cost_item_id,
                    name=li.name,
                    description=li.description,
                    item_type=li.item_type,
                    quantity=li.quantity,
                    unit=li.unit,
                    unit_cost=li.unit_cost,
                    unit_price=li.unit_price,
                    total_cost=li.total_cost,
                    total_price=li.total_price,
                    markup_pct=li.markup_pct,
                    taxable=li.taxable,
                    cost_code=li.cost_code,
                    notes=li.notes,
                    display_order=li.display_order,
                )
                self.db.add(new_li)

        # Copy markups
        for markup in original.markups:
            new_markup = EstimateMarkup(
                estimate_id=new_est.id,
                company_id=self.company_id,
                name=markup.name,
                markup_type=markup.markup_type,
                value=markup.value,
                apply_before_tax=markup.apply_before_tax,
                is_compounding=markup.is_compounding,
                display_order=markup.display_order,
                calculated_amount=markup.calculated_amount,
            )
            self.db.add(new_markup)

        self.db.commit()

        # Recalculate the new version
        self.recalculate_estimate(new_est.id)
        self.db.refresh(new_est)
        return new_est

    # =========================================================================
    # SEND TO BUDGET
    # =========================================================================

    def send_to_budget(self, estimate_id: int) -> dict:
        """Create budget line items from estimate lines, grouped by cost_code.

        Groups estimate line items by cost_code and creates/updates budget
        records in the agcm_finance module (if available). Returns a summary.
        """
        estimate = self.get_estimate(estimate_id)
        if not estimate:
            return {"success": False, "message": "Estimate not found"}

        line_items = (
            self.db.query(EstimateLineItem)
            .filter(
                EstimateLineItem.estimate_id == estimate_id,
                EstimateLineItem.cost_code.isnot(None),
                EstimateLineItem.cost_code != "",
            )
            .all()
        )

        # Group by cost_code
        budget_lines = {}
        for li in line_items:
            code = li.cost_code
            if code not in budget_lines:
                budget_lines[code] = {
                    "cost_code": code,
                    "planned_amount": 0,
                    "description": li.name,
                    "line_count": 0,
                }
            budget_lines[code]["planned_amount"] += li.total_cost
            budget_lines[code]["line_count"] += 1

        # Create/update budget records in agcm_finance module
        created_count = 0
        updated_count = 0
        try:
            from addons.agcm_finance.models.budget import Budget
            from addons.agcm_finance.models.cost_code import CostCode

            for code, bl in budget_lines.items():
                # Look up cost_code_id from the CostCode table
                cost_code_obj = (
                    self.db.query(CostCode)
                    .filter(
                        CostCode.code == code,
                        CostCode.project_id == estimate.project_id,
                        CostCode.company_id == self.company_id,
                    )
                    .first()
                )
                cost_code_id = cost_code_obj.id if cost_code_obj else None

                # UPSERT: check if budget line already exists
                existing = (
                    (
                        self.db.query(Budget)
                        .filter(
                            Budget.project_id == estimate.project_id,
                            Budget.cost_code_id == cost_code_id,
                            Budget.company_id == self.company_id,
                        )
                        .first()
                    )
                    if cost_code_id
                    else None
                )

                desc = f"From Estimate {estimate.sequence_name} - {bl['description']}"

                if existing:
                    existing.planned_amount = bl["planned_amount"]
                    existing.description = desc
                    updated_count += 1
                else:
                    new_budget = Budget(
                        project_id=estimate.project_id,
                        cost_code_id=cost_code_id,
                        description=desc,
                        planned_amount=bl["planned_amount"],
                        actual_amount=0,
                        committed_amount=0,
                        company_id=self.company_id,
                    )
                    self.db.add(new_budget)
                    created_count += 1

            self.db.commit()
            logger.info(
                "Budget export: created=%d, updated=%d, total: %.2f",
                created_count,
                updated_count,
                sum(b["planned_amount"] for b in budget_lines.values()),
            )
        except ImportError:
            logger.warning(
                "agcm_finance module not installed — budget integration skipped"
            )
            created_count = len(budget_lines)
        except Exception as e:
            logger.warning("Budget integration error: %s", e)
            created_count = len(budget_lines)

        return {
            "success": True,
            "message": f"Exported {created_count} budget lines from estimate",
            "budget_lines": list(budget_lines.values()),
            "total_planned": sum(b["planned_amount"] for b in budget_lines.values()),
        }

    # =========================================================================
    # APPROVE ESTIMATE
    # =========================================================================

    def approve_estimate(self, estimate_id: int) -> Optional[Estimate]:
        estimate = self.get_estimate(estimate_id)
        if not estimate:
            return None
        estimate.status = EstimateStatus.APPROVED.value
        estimate.approved_by = self.user_id
        estimate.approved_date = date.today()
        estimate.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(estimate)
        return estimate

    # =========================================================================
    # ADD ASSEMBLY TO ESTIMATE
    # =========================================================================

    def add_assembly_to_estimate(
        self,
        estimate_id: int,
        group_id: int,
        assembly_id: int,
        quantity_multiplier: float = 1.0,
    ) -> list:
        """Expand assembly items into estimate line items within a group."""
        # Verify estimate belongs to this company (IDOR protection)
        estimate = self.get_estimate(estimate_id)
        if not estimate:
            return []
        # Verify group belongs to this estimate and company
        group = (
            self.db.query(EstimateGroup)
            .filter(
                EstimateGroup.id == group_id,
                EstimateGroup.estimate_id == estimate_id,
                EstimateGroup.company_id == self.company_id,
            )
            .first()
        )
        if not group:
            return []
        assembly = self.get_assembly(assembly_id)
        if not assembly:
            return []

        # Get max display_order in group
        max_order = (
            self.db.query(func.max(EstimateLineItem.display_order))
            .filter(EstimateLineItem.group_id == group_id)
            .scalar()
            or 0
        )

        created_items = []
        for idx, ai in enumerate(assembly.items):
            effective_qty = ai.quantity * quantity_multiplier
            waste_mult = 1 + (ai.waste_factor / 100) if ai.waste_factor else 1
            adjusted_qty = effective_qty * waste_mult

            li = EstimateLineItem(
                group_id=group_id,
                estimate_id=estimate_id,
                company_id=self.company_id,
                cost_item_id=ai.cost_item_id,
                name=ai.name,
                description=ai.description or f"From assembly: {assembly.name}",
                item_type=ai.item_type,
                quantity=round(adjusted_qty, 4),
                unit=ai.unit,
                unit_cost=ai.unit_cost,
                unit_price=ai.unit_cost,  # will be recalculated
                total_cost=round(adjusted_qty * ai.unit_cost, 2),
                total_price=round(adjusted_qty * ai.unit_cost, 2),
                display_order=max_order + idx + 1,
            )
            self.db.add(li)
            created_items.append(li)

        self.db.commit()

        # Recalculate estimate totals
        self.recalculate_estimate(estimate_id)

        for item in created_items:
            self.db.refresh(item)
        return created_items

    # =========================================================================
    # GENERATE PROPOSAL
    # =========================================================================

    def generate_proposal(
        self, estimate_id: int, data: ProposalCreate
    ) -> Optional[Proposal]:
        estimate = self.get_estimate(estimate_id)
        if not estimate:
            return None

        proposal = Proposal(
            company_id=self.company_id,
            sequence_name=self._next_sequence(Proposal, "PROP"),
            estimate_id=estimate_id,
            project_id=data.project_id or estimate.project_id,
            name=data.name,
            description=data.description,
            client_name=data.client_name,
            client_email=data.client_email,
            client_phone=data.client_phone,
            scope_of_work=data.scope_of_work,
            terms_and_conditions=data.terms_and_conditions,
            exclusions=data.exclusions,
            payment_schedule=data.payment_schedule,
            valid_until=data.valid_until,
            show_line_items=data.show_line_items,
            show_unit_prices=data.show_unit_prices,
            show_markup=data.show_markup,
            show_groups=data.show_groups,
            notes=data.notes,
            created_by=self.user_id,
        )
        self.db.add(proposal)
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    # =========================================================================
    # ESTIMATE GROUP CRUD
    # =========================================================================

    def create_group(self, data: EstimateGroupCreate) -> EstimateGroup:
        # Verify estimate belongs to this company (IDOR protection)
        estimate = self.get_estimate(data.estimate_id)
        if not estimate:
            raise ValueError("Estimate not found or access denied")
        group = EstimateGroup(
            estimate_id=data.estimate_id,
            company_id=self.company_id,
            name=data.name,
            description=data.description,
            display_order=data.display_order,
        )
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        return group

    def update_group(
        self, group_id: int, data: EstimateGroupUpdate
    ) -> Optional[EstimateGroup]:
        group = (
            self.db.query(EstimateGroup)
            .filter(
                EstimateGroup.id == group_id,
                EstimateGroup.company_id == self.company_id,
            )
            .first()
        )
        if not group:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(group, key, value)
        self.db.commit()
        self.db.refresh(group)
        return group

    def delete_group(self, group_id: int) -> Optional[int]:
        """Delete group and return the estimate_id for recalculation."""
        group = (
            self.db.query(EstimateGroup)
            .filter(
                EstimateGroup.id == group_id,
                EstimateGroup.company_id == self.company_id,
            )
            .first()
        )
        if not group:
            return None
        estimate_id = group.estimate_id
        self.db.delete(group)
        self.db.commit()
        self.recalculate_estimate(estimate_id)
        return estimate_id

    # =========================================================================
    # ESTIMATE LINE ITEM CRUD
    # =========================================================================

    def list_line_items(
        self,
        estimate_id: int = None,
        group_id: int = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        page_size = min(page_size, 200)
        q = self.db.query(EstimateLineItem).filter(
            EstimateLineItem.company_id == self.company_id
        )
        if estimate_id:
            q = q.filter(EstimateLineItem.estimate_id == estimate_id)
        if group_id:
            q = q.filter(EstimateLineItem.group_id == group_id)
        total = q.count()
        items = (
            q.order_by(EstimateLineItem.display_order, EstimateLineItem.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "items": [EstimateLineItemResponse.model_validate(i).model_dump() for i in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def create_line_item(self, data: EstimateLineItemCreate) -> EstimateLineItem:
        # Verify estimate belongs to this company (IDOR protection)
        estimate = self.get_estimate(data.estimate_id)
        if not estimate:
            raise ValueError("Estimate not found or access denied")
        # Verify group belongs to this estimate
        group = (
            self.db.query(EstimateGroup)
            .filter(
                EstimateGroup.id == data.group_id,
                EstimateGroup.estimate_id == data.estimate_id,
                EstimateGroup.company_id == self.company_id,
            )
            .first()
        )
        if not group:
            raise ValueError("Group not found or does not belong to this estimate")

        unit_price = data.unit_price
        if unit_price is None:
            unit_price = data.unit_cost * (1 + (data.markup_pct or 0) / 100)

        li = EstimateLineItem(
            group_id=data.group_id,
            estimate_id=data.estimate_id,
            company_id=self.company_id,
            cost_item_id=data.cost_item_id,
            name=data.name,
            description=data.description,
            item_type=data.item_type,
            quantity=data.quantity,
            unit=data.unit,
            unit_cost=data.unit_cost,
            unit_price=unit_price,
            total_cost=data.quantity * data.unit_cost,
            total_price=data.quantity * unit_price,
            markup_pct=data.markup_pct,
            taxable=data.taxable,
            cost_code=data.cost_code,
            notes=data.notes,
            display_order=data.display_order,
        )
        self.db.add(li)
        self.db.commit()
        self.db.refresh(li)

        # Auto-recalculate
        self.recalculate_estimate(data.estimate_id)
        self.db.refresh(li)
        return li

    def update_line_item(
        self, item_id: int, data: EstimateLineItemUpdate
    ) -> Optional[EstimateLineItem]:
        li = (
            self.db.query(EstimateLineItem)
            .filter(
                EstimateLineItem.id == item_id,
                EstimateLineItem.company_id == self.company_id,
            )
            .first()
        )
        if not li:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(li, key, value)
        self.db.commit()

        # Auto-recalculate
        self.recalculate_estimate(li.estimate_id)
        self.db.refresh(li)
        return li

    def delete_line_item(self, item_id: int) -> Optional[int]:
        """Delete line item and return the estimate_id for recalculation."""
        li = (
            self.db.query(EstimateLineItem)
            .filter(
                EstimateLineItem.id == item_id,
                EstimateLineItem.company_id == self.company_id,
            )
            .first()
        )
        if not li:
            return None
        estimate_id = li.estimate_id
        self.db.delete(li)
        self.db.commit()
        self.recalculate_estimate(estimate_id)
        return estimate_id

    # =========================================================================
    # ESTIMATE MARKUP CRUD
    # =========================================================================

    def create_markup(self, data: EstimateMarkupCreate) -> EstimateMarkup:
        # Verify estimate belongs to this company (IDOR protection)
        estimate = self.get_estimate(data.estimate_id)
        if not estimate:
            raise ValueError("Estimate not found or access denied")
        markup = EstimateMarkup(
            estimate_id=data.estimate_id,
            company_id=self.company_id,
            name=data.name,
            markup_type=data.markup_type,
            value=data.value,
            apply_before_tax=data.apply_before_tax,
            is_compounding=data.is_compounding,
            display_order=data.display_order,
        )
        self.db.add(markup)
        self.db.commit()
        self.db.refresh(markup)

        self.recalculate_estimate(data.estimate_id)
        self.db.refresh(markup)
        return markup

    def update_markup(
        self, markup_id: int, data: EstimateMarkupUpdate
    ) -> Optional[EstimateMarkup]:
        markup = (
            self.db.query(EstimateMarkup)
            .filter(
                EstimateMarkup.id == markup_id,
                EstimateMarkup.company_id == self.company_id,
            )
            .first()
        )
        if not markup:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(markup, key, value)
        self.db.commit()

        self.recalculate_estimate(markup.estimate_id)
        self.db.refresh(markup)
        return markup

    def delete_markup(self, markup_id: int) -> Optional[int]:
        markup = (
            self.db.query(EstimateMarkup)
            .filter(
                EstimateMarkup.id == markup_id,
                EstimateMarkup.company_id == self.company_id,
            )
            .first()
        )
        if not markup:
            return None
        estimate_id = markup.estimate_id
        self.db.delete(markup)
        self.db.commit()
        self.recalculate_estimate(estimate_id)
        return estimate_id

    # =========================================================================
    # PROPOSAL CRUD
    # =========================================================================

    def list_proposals(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        query = self.db.query(Proposal).filter(Proposal.company_id == self.company_id)
        if project_id:
            query = query.filter(Proposal.project_id == project_id)
        if status:
            query = query.filter(Proposal.status == status)
        total = query.count()
        items = (
            query.order_by(Proposal.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_proposal(self, proposal_id: int) -> Optional[Proposal]:
        return (
            self.db.query(Proposal)
            .filter(
                Proposal.id == proposal_id,
                Proposal.company_id == self.company_id,
            )
            .first()
        )

    def update_proposal(
        self, proposal_id: int, data: ProposalUpdate
    ) -> Optional[Proposal]:
        proposal = self.get_proposal(proposal_id)
        if not proposal:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(proposal, key, value)
        proposal.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def delete_proposal(self, proposal_id: int) -> bool:
        proposal = self.get_proposal(proposal_id)
        if not proposal:
            return False
        self.db.delete(proposal)
        self.db.commit()
        return True

    def send_proposal(self, proposal_id: int) -> Optional[Proposal]:
        proposal = self.get_proposal(proposal_id)
        if not proposal:
            return None
        proposal.status = ProposalStatus.SENT.value
        proposal.sent_date = date.today()
        proposal.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def approve_proposal(self, proposal_id: int) -> Optional[Proposal]:
        proposal = self.get_proposal(proposal_id)
        if not proposal:
            return None
        proposal.status = ProposalStatus.APPROVED.value
        proposal.approved_date = date.today()
        proposal.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def reject_proposal(self, proposal_id: int) -> Optional[Proposal]:
        proposal = self.get_proposal(proposal_id)
        if not proposal:
            return None
        proposal.status = ProposalStatus.REJECTED.value
        proposal.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    # =========================================================================
    # TAKEOFF CRUD
    # =========================================================================

    def list_takeoff_sheets(
        self, project_id: Optional[int] = None, page: int = 1, page_size: int = 20
    ) -> dict:
        query = self.db.query(TakeoffSheet).filter(
            TakeoffSheet.company_id == self.company_id
        )
        if project_id:
            query = query.filter(TakeoffSheet.project_id == project_id)
        total = query.count()
        items = (
            query.order_by(TakeoffSheet.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_takeoff_sheet(self, sheet_id: int) -> Optional[TakeoffSheet]:
        return (
            self.db.query(TakeoffSheet)
            .filter(
                TakeoffSheet.id == sheet_id,
                TakeoffSheet.company_id == self.company_id,
            )
            .first()
        )

    def create_takeoff_sheet(self, data: TakeoffSheetCreate) -> TakeoffSheet:
        sheet = TakeoffSheet(
            company_id=self.company_id,
            sequence_name=self._next_sequence(TakeoffSheet, "TO"),
            project_id=data.project_id,
            name=data.name,
            description=data.description,
            file_name=data.file_name,
            file_url=data.file_url,
            document_id=data.document_id,
            page_number=data.page_number,
            scale_factor=data.scale_factor,
            scale_unit=data.scale_unit,
            created_by=self.user_id,
        )
        self.db.add(sheet)
        self.db.commit()
        self.db.refresh(sheet)
        return sheet

    def update_takeoff_sheet(
        self, sheet_id: int, data: TakeoffSheetUpdate
    ) -> Optional[TakeoffSheet]:
        sheet = self.get_takeoff_sheet(sheet_id)
        if not sheet:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(sheet, key, value)
        sheet.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(sheet)
        return sheet

    def delete_takeoff_sheet(self, sheet_id: int) -> bool:
        sheet = self.get_takeoff_sheet(sheet_id)
        if not sheet:
            return False
        self.db.delete(sheet)
        self.db.commit()
        return True

    def list_measurements(
        self, sheet_id: Optional[int] = None, page: int = 1, page_size: int = 20
    ) -> dict:
        query = self.db.query(TakeoffMeasurement).filter(
            TakeoffMeasurement.company_id == self.company_id
        )
        if sheet_id:
            query = query.filter(TakeoffMeasurement.sheet_id == sheet_id)
        total = query.count()
        items = (
            query.order_by(TakeoffMeasurement.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def create_measurement(self, data: TakeoffMeasurementCreate) -> TakeoffMeasurement:
        measurement = TakeoffMeasurement(
            sheet_id=data.sheet_id,
            company_id=self.company_id,
            estimate_line_item_id=data.estimate_line_item_id,
            measurement_type=data.measurement_type,
            label=data.label,
            value=data.value,
            unit=data.unit,
            points_json=data.points_json,
            color=data.color,
            layer=data.layer,
        )
        self.db.add(measurement)
        self.db.commit()
        self.db.refresh(measurement)
        return measurement

    def update_measurement(
        self, measurement_id: int, data: TakeoffMeasurementUpdate
    ) -> Optional[TakeoffMeasurement]:
        m = (
            self.db.query(TakeoffMeasurement)
            .filter(
                TakeoffMeasurement.id == measurement_id,
                TakeoffMeasurement.company_id == self.company_id,
            )
            .first()
        )
        if not m:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(m, key, value)
        self.db.commit()
        self.db.refresh(m)
        return m

    def delete_measurement(self, measurement_id: int) -> bool:
        m = (
            self.db.query(TakeoffMeasurement)
            .filter(
                TakeoffMeasurement.id == measurement_id,
                TakeoffMeasurement.company_id == self.company_id,
            )
            .first()
        )
        if not m:
            return False
        self.db.delete(m)
        self.db.commit()
        return True

    def link_measurement_to_line(
        self, measurement_id: int, line_item_id: int
    ) -> Optional[TakeoffMeasurement]:
        m = (
            self.db.query(TakeoffMeasurement)
            .filter(
                TakeoffMeasurement.id == measurement_id,
                TakeoffMeasurement.company_id == self.company_id,
            )
            .first()
        )
        if not m:
            return None
        # Verify line item belongs to this company (IDOR protection)
        li = (
            self.db.query(EstimateLineItem)
            .filter(
                EstimateLineItem.id == line_item_id,
                EstimateLineItem.company_id == self.company_id,
            )
            .first()
        )
        if not li:
            return None
        m.estimate_line_item_id = line_item_id
        self.db.commit()
        self.db.refresh(m)
        return m
