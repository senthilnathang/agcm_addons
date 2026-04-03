"""Procurement service — business logic for POs, Subcontracts, and Vendor Bills."""

import logging
import re
from datetime import date
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from addons.agcm_procurement.models.purchase_order import (
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseOrderStatus,
)
from addons.agcm_procurement.models.subcontract import (
    Subcontract,
    SubcontractSOVLine,
    SubcontractComplianceDoc,
    SubcontractStatus,
)
from addons.agcm_procurement.models.vendor_bill import (
    VendorBill,
    VendorBillLine,
    VendorBillPayment,
    VendorBillStatus,
)
from addons.agcm_procurement.schemas.procurement import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderLineCreate,
    PurchaseOrderLineUpdate,
    SubcontractCreate,
    SubcontractUpdate,
    SubcontractSOVLineCreate,
    SubcontractSOVLineUpdate,
    ComplianceDocCreate,
    ComplianceDocUpdate,
    VendorBillCreate,
    VendorBillUpdate,
    VendorBillLineCreate,
    VendorBillLineUpdate,
    VendorBillPaymentCreate,
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

# Sequence configuration: (prefix, padding)
SEQUENCE_CONFIG = {
    "agcm_purchase_orders": ("PO", 5),
    "agcm_subcontracts": ("SC", 5),
    "agcm_vendor_bills": ("VB", 5),
}


def _next_sequence(db: Session, model_class, company_id: int) -> str:
    """Generate the next sequence_name for a procurement model."""
    tablename = model_class.__tablename__
    config = SEQUENCE_CONFIG.get(tablename)
    if not config:
        return None

    prefix, padding = config

    last = (
        db.query(model_class.sequence_name)
        .filter(model_class.company_id == company_id)
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


class ProcurementService:
    """Handles Purchase Order, Subcontract, and Vendor Bill CRUD and business logic."""

    def __init__(self, db: Session, company_id: int, user_id: int):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id

    def _invalidate_procurement_cache(self, project_id: int = None):
        """Invalidate procurement-related cache."""
        if not CACHE_AVAILABLE:
            return

        if project_id:
            cache.invalidate_pattern_distributed(
                f"agcm_procurement:project:{self.company_id}:{project_id}:*"
            )
        cache.invalidate_pattern_distributed(f"agcm_procurement:*")

    # =========================================================================
    # PURCHASE ORDERS
    # =========================================================================

    def list_purchase_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict:
        page_size = min(page_size, 200)
        query = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.company_id == self.company_id,
            PurchaseOrder.is_deleted == False,
        )

        if project_id:
            query = query.filter(PurchaseOrder.project_id == project_id)
        if status:
            query = query.filter(PurchaseOrder.status == status)
        if search:
            term = f"%{search}%"
            query = query.filter(
                (PurchaseOrder.vendor_name.ilike(term))
                | (PurchaseOrder.po_number.ilike(term))
                | (PurchaseOrder.sequence_name.ilike(term))
            )

        total = query.count()
        skip = (page - 1) * page_size
        items = (
            query.order_by(PurchaseOrder.id.desc()).offset(skip).limit(page_size).all()
        )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_purchase_order(self, po_id: int) -> Optional[PurchaseOrder]:
        return (
            self.db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.id == po_id,
                PurchaseOrder.company_id == self.company_id,
                PurchaseOrder.is_deleted == False,
            )
            .first()
        )

    def get_purchase_order_detail(self, po_id: int) -> Optional[dict]:
        po = self.get_purchase_order(po_id)
        if not po:
            return None

        lines = sorted(po.lines or [], key=lambda l: l.display_order)
        total_qty = sum(l.quantity for l in lines) if lines else 0
        total_received = sum(l.received_qty for l in lines) if lines else 0
        received_pct = (total_received / total_qty * 100) if total_qty > 0 else 0

        return {
            **{c.key: getattr(po, c.key) for c in po.__table__.columns},
            "lines": lines,
            "received_pct": round(received_pct, 1),
            "line_count": len(lines),
        }

    def create_purchase_order(self, data: PurchaseOrderCreate) -> PurchaseOrder:
        po = PurchaseOrder(
            company_id=self.company_id,
            project_id=data.project_id,
            sequence_name=_next_sequence(self.db, PurchaseOrder, self.company_id),
            po_number=data.po_number,
            vendor_name=data.vendor_name,
            vendor_contact=data.vendor_contact,
            status=data.status or "draft",
            description=data.description,
            issue_date=data.issue_date,
            expected_delivery=data.expected_delivery,
            actual_delivery=data.actual_delivery,
            shipping_method=data.shipping_method,
            shipping_address=data.shipping_address,
            tax_amount=data.tax_amount,
            retainage_pct=data.retainage_pct,
            estimate_id=data.estimate_id,
            notes=data.notes,
            created_by=self.user_id,
        )

        self.db.add(po)
        self.db.flush()

        # Create lines
        for line_data in data.lines or []:
            line = PurchaseOrderLine(
                po_id=po.id,
                company_id=self.company_id,
                cost_code=line_data.cost_code,
                description=line_data.description,
                item_type=line_data.item_type,
                quantity=line_data.quantity,
                unit=line_data.unit,
                unit_cost=line_data.unit_cost,
                total_cost=line_data.total_cost
                or (line_data.quantity * line_data.unit_cost),
                display_order=line_data.display_order,
                notes=line_data.notes,
            )
            self.db.add(line)

        self.db.flush()
        self._recalculate_po(po)
        self.db.commit()
        self.db.refresh(po)
        return po

    def update_purchase_order(
        self, po_id: int, data: PurchaseOrderUpdate
    ) -> Optional[PurchaseOrder]:
        po = self.get_purchase_order(po_id)
        if not po:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(po, key, value)
        po.updated_by = self.user_id

        self._recalculate_po(po)
        self.db.commit()
        self.db.refresh(po)
        return po

    def delete_purchase_order(self, po_id: int) -> bool:
        po = self.get_purchase_order(po_id)
        if not po:
            return False
        self.db.delete(po)
        self.db.commit()
        return True

    def approve_po(self, po_id: int) -> Optional[PurchaseOrder]:
        po = self.get_purchase_order(po_id)
        if not po:
            return None

        # Try approval chain
        from addons.agcm.services.approval_integration import submit_for_approval
        tasks = submit_for_approval(
            db=self.db,
            entity_type="purchase_order",
            entity_id=po.id,
            requester_id=self.user_id,
            company_id=self.company_id,
            amount=getattr(po, "total_amount", None),
        )
        if tasks:
            po.status = PurchaseOrderStatus.PENDING_APPROVAL.value
            po.updated_by = self.user_id
            self.db.commit()
            self.db.refresh(po)
            return po

        # No chain configured — auto-approve
        return self._finalize_po_approval(po)

    def _finalize_po_approval(self, po: PurchaseOrder) -> PurchaseOrder:
        po.status = PurchaseOrderStatus.APPROVED.value
        po.approved_by = self.user_id
        po.approved_date = date.today()
        po.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(po)
        return po

    def receive_delivery(
        self, po_id: int, line_updates: list
    ) -> Optional[PurchaseOrder]:
        """Update received_qty on PO lines and recalculate PO status."""
        po = self.get_purchase_order(po_id)
        if not po:
            return None

        for update in line_updates:
            line_id = update.get("line_id")
            received_qty = update.get("received_qty", 0)
            if line_id is None:
                continue
            line = (
                self.db.query(PurchaseOrderLine)
                .filter(
                    PurchaseOrderLine.id == line_id,
                    PurchaseOrderLine.po_id == po_id,
                )
                .first()
            )
            if line:
                line.received_qty = received_qty

        # Determine status based on received quantities
        lines = po.lines or []
        if lines:
            all_received = all(l.received_qty >= l.quantity for l in lines)
            any_received = any(l.received_qty > 0 for l in lines)
            if all_received:
                po.status = PurchaseOrderStatus.RECEIVED.value
                po.actual_delivery = date.today()
            elif any_received:
                po.status = PurchaseOrderStatus.PARTIALLY_RECEIVED.value

        po.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(po)
        return po

    def create_po_from_estimate(
        self, estimate_id: int, vendor_name: str
    ) -> Optional[PurchaseOrder]:
        """Create a PO from an estimate's line items."""
        from addons.agcm_estimate.models.estimate import Estimate, EstimateLineItem

        estimate = (
            self.db.query(Estimate)
            .filter(
                Estimate.id == estimate_id,
                Estimate.company_id == self.company_id,
            )
            .first()
        )
        if not estimate:
            return None

        line_items = (
            self.db.query(EstimateLineItem)
            .filter(EstimateLineItem.estimate_id == estimate_id)
            .order_by(EstimateLineItem.id)
            .all()
        )

        po = PurchaseOrder(
            company_id=self.company_id,
            project_id=estimate.project_id,
            sequence_name=_next_sequence(self.db, PurchaseOrder, self.company_id),
            vendor_name=vendor_name,
            status="draft",
            description=f"Created from estimate: {estimate.name}",
            estimate_id=estimate_id,
            created_by=self.user_id,
        )
        self.db.add(po)
        self.db.flush()

        for idx, item in enumerate(line_items):
            total = (item.quantity or 0) * (item.unit_cost or 0)
            line = PurchaseOrderLine(
                po_id=po.id,
                company_id=self.company_id,
                cost_code=getattr(item, "cost_code", None),
                description=item.description or "Item",
                item_type=getattr(item, "item_type", "material") or "material",
                quantity=item.quantity or 0,
                unit=getattr(item, "unit", "ea") or "ea",
                unit_cost=item.unit_cost or 0,
                total_cost=total,
                display_order=idx,
            )
            self.db.add(line)

        self.db.flush()
        self._recalculate_po(po)
        self.db.commit()
        self.db.refresh(po)
        return po

    def _recalculate_po(self, po: PurchaseOrder):
        """Recalculate PO subtotal, total_amount, retainage from lines."""
        lines = (
            self.db.query(PurchaseOrderLine)
            .filter(PurchaseOrderLine.po_id == po.id)
            .all()
        )
        subtotal = sum(l.total_cost for l in lines)
        po.subtotal = subtotal
        po.total_amount = subtotal + (po.tax_amount or 0)
        po.retainage_amount = subtotal * (po.retainage_pct or 0) / 100.0

    def recalculate_po(self, po_id: int) -> Optional[PurchaseOrder]:
        po = self.get_purchase_order(po_id)
        if not po:
            return None
        self._recalculate_po(po)
        self.db.commit()
        self.db.refresh(po)
        return po

    # -- PO Lines --

    def create_po_line(
        self, data: PurchaseOrderLineCreate, po_id: int
    ) -> Optional[PurchaseOrderLine]:
        po = self.get_purchase_order(po_id)
        if not po:
            return None

        line = PurchaseOrderLine(
            po_id=po_id,
            company_id=self.company_id,
            cost_code=data.cost_code,
            description=data.description,
            item_type=data.item_type,
            quantity=data.quantity,
            unit=data.unit,
            unit_cost=data.unit_cost,
            total_cost=data.total_cost or (data.quantity * data.unit_cost),
            display_order=data.display_order,
            notes=data.notes,
        )
        self.db.add(line)
        self.db.flush()
        self._recalculate_po(po)
        self.db.commit()
        self.db.refresh(line)
        return line

    def update_po_line(
        self, line_id: int, data: PurchaseOrderLineUpdate
    ) -> Optional[PurchaseOrderLine]:
        line = (
            self.db.query(PurchaseOrderLine)
            .join(PurchaseOrder)
            .filter(
                PurchaseOrderLine.id == line_id,
                PurchaseOrder.company_id == self.company_id,
            )
            .first()
        )
        if not line:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(line, key, value)

        po = self.get_purchase_order(line.po_id)
        if po:
            self._recalculate_po(po)

        self.db.commit()
        self.db.refresh(line)
        return line

    def delete_po_line(self, line_id: int) -> bool:
        line = (
            self.db.query(PurchaseOrderLine)
            .join(PurchaseOrder)
            .filter(
                PurchaseOrderLine.id == line_id,
                PurchaseOrder.company_id == self.company_id,
            )
            .first()
        )
        if not line:
            return False

        po_id = line.po_id
        self.db.delete(line)
        self.db.flush()

        po = self.get_purchase_order(po_id)
        if po:
            self._recalculate_po(po)

        self.db.commit()
        return True

    # =========================================================================
    # SUBCONTRACTS
    # =========================================================================

    def list_subcontracts(
        self,
        page: int = 1,
        page_size: int = 20,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict:
        page_size = min(page_size, 200)
        query = self.db.query(Subcontract).filter(
            Subcontract.company_id == self.company_id,
            Subcontract.is_deleted == False,
        )

        if project_id:
            query = query.filter(Subcontract.project_id == project_id)
        if status:
            query = query.filter(Subcontract.status == status)
        if search:
            term = f"%{search}%"
            query = query.filter(
                (Subcontract.vendor_name.ilike(term))
                | (Subcontract.contract_number.ilike(term))
                | (Subcontract.sequence_name.ilike(term))
            )

        total = query.count()
        skip = (page - 1) * page_size
        items = (
            query.order_by(Subcontract.id.desc()).offset(skip).limit(page_size).all()
        )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_subcontract(self, sc_id: int) -> Optional[Subcontract]:
        return (
            self.db.query(Subcontract)
            .filter(
                Subcontract.id == sc_id,
                Subcontract.company_id == self.company_id,
                Subcontract.is_deleted == False,
            )
            .first()
        )

    def get_subcontract_detail(self, sc_id: int) -> Optional[dict]:
        sc = self.get_subcontract(sc_id)
        if not sc:
            return None

        sov_lines = sorted(sc.sov_lines or [], key=lambda l: l.display_order)
        compliance_docs = sc.compliance_docs or []

        return {
            **{c.key: getattr(sc, c.key) for c in sc.__table__.columns},
            "sov_lines": sov_lines,
            "compliance_docs": compliance_docs,
            "sov_count": len(sov_lines),
            "compliance_count": len(compliance_docs),
        }

    def create_subcontract(self, data: SubcontractCreate) -> Subcontract:
        sc = Subcontract(
            company_id=self.company_id,
            project_id=data.project_id,
            sequence_name=_next_sequence(self.db, Subcontract, self.company_id),
            contract_number=data.contract_number,
            vendor_name=data.vendor_name,
            vendor_contact=data.vendor_contact,
            status=data.status or "draft",
            scope_of_work=data.scope_of_work,
            start_date=data.start_date,
            end_date=data.end_date,
            original_amount=data.original_amount,
            approved_cos=data.approved_cos,
            revised_amount=data.original_amount + data.approved_cos,
            balance_remaining=data.original_amount + data.approved_cos,
            retainage_pct=data.retainage_pct,
            estimate_id=data.estimate_id,
            notes=data.notes,
            created_by=self.user_id,
        )

        self.db.add(sc)
        self.db.flush()

        for line_data in data.sov_lines or []:
            sov = SubcontractSOVLine(
                subcontract_id=sc.id,
                company_id=self.company_id,
                cost_code=line_data.cost_code,
                description=line_data.description,
                scheduled_value=line_data.scheduled_value,
                billed_previous=line_data.billed_previous,
                billed_current=line_data.billed_current,
                stored_materials=line_data.stored_materials,
                display_order=line_data.display_order,
                source_type=line_data.source_type,
            )
            self._calculate_sov_line(sov, sc.retainage_pct)
            self.db.add(sov)

        self.db.flush()
        self._recalculate_subcontract(sc)
        self.db.commit()
        self.db.refresh(sc)
        return sc

    def update_subcontract(
        self, sc_id: int, data: SubcontractUpdate
    ) -> Optional[Subcontract]:
        sc = self.get_subcontract(sc_id)
        if not sc:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(sc, key, value)
        sc.updated_by = self.user_id

        sc.revised_amount = sc.original_amount + sc.approved_cos
        self._recalculate_subcontract(sc)
        self.db.commit()
        self.db.refresh(sc)
        return sc

    def delete_subcontract(self, sc_id: int) -> bool:
        sc = self.get_subcontract(sc_id)
        if not sc:
            return False
        self.db.delete(sc)
        self.db.commit()
        return True

    def approve_subcontract(self, sc_id: int) -> Optional[Subcontract]:
        sc = self.get_subcontract(sc_id)
        if not sc:
            return None

        from addons.agcm.services.approval_integration import submit_for_approval
        tasks = submit_for_approval(
            db=self.db,
            entity_type="subcontract",
            entity_id=sc.id,
            requester_id=self.user_id,
            company_id=self.company_id,
            amount=getattr(sc, "contract_amount", None),
        )
        if tasks:
            sc.status = SubcontractStatus.PENDING_APPROVAL.value
            sc.updated_by = self.user_id
            self.db.commit()
            self.db.refresh(sc)
            return sc

        return self._finalize_subcontract_approval(sc)

    def _finalize_subcontract_approval(self, sc: Subcontract) -> Subcontract:
        sc.status = SubcontractStatus.APPROVED.value
        sc.approved_by = self.user_id
        sc.approved_date = date.today()
        sc.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(sc)
        return sc

    def update_sov_billing(
        self, sc_id: int, sov_updates: list
    ) -> Optional[Subcontract]:
        """Update billed_current on SOV lines and recalculate subcontract totals."""
        sc = self.get_subcontract(sc_id)
        if not sc:
            return None

        for update in sov_updates:
            line_id = update.get("line_id")
            if line_id is None:
                continue
            sov = (
                self.db.query(SubcontractSOVLine)
                .filter(
                    SubcontractSOVLine.id == line_id,
                    SubcontractSOVLine.subcontract_id == sc_id,
                )
                .first()
            )
            if sov:
                sov.billed_current = update.get("billed_current", sov.billed_current)
                sov.stored_materials = update.get(
                    "stored_materials", sov.stored_materials
                )
                self._calculate_sov_line(sov, sc.retainage_pct)

        self._recalculate_subcontract(sc)
        sc.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(sc)
        return sc

    def _calculate_sov_line(self, sov: SubcontractSOVLine, retainage_pct: float):
        """Recalculate computed fields on an SOV line."""
        sov.total_completed = (
            sov.billed_previous + sov.billed_current + sov.stored_materials
        )
        sov.pct_complete = (
            (sov.total_completed / sov.scheduled_value * 100)
            if sov.scheduled_value > 0
            else 0
        )
        sov.retainage = sov.total_completed * (retainage_pct or 0) / 100.0
        sov.balance_to_finish = sov.scheduled_value - sov.total_completed

    def _recalculate_subcontract(self, sc: Subcontract):
        """Recalculate subcontract totals from SOV lines."""
        lines = (
            self.db.query(SubcontractSOVLine)
            .filter(SubcontractSOVLine.subcontract_id == sc.id)
            .all()
        )
        sc.billed_to_date = sum(l.total_completed for l in lines)
        sc.retainage_held = sum(l.retainage for l in lines)
        sc.balance_remaining = sc.revised_amount - sc.billed_to_date

    # -- SOV Lines --

    def create_sov_line(
        self, data: SubcontractSOVLineCreate, subcontract_id: int
    ) -> Optional[SubcontractSOVLine]:
        sc = self.get_subcontract(subcontract_id)
        if not sc:
            return None

        sov = SubcontractSOVLine(
            subcontract_id=subcontract_id,
            company_id=self.company_id,
            cost_code=data.cost_code,
            description=data.description,
            scheduled_value=data.scheduled_value,
            billed_previous=data.billed_previous,
            billed_current=data.billed_current,
            stored_materials=data.stored_materials,
            display_order=data.display_order,
            source_type=data.source_type,
        )
        self._calculate_sov_line(sov, sc.retainage_pct)
        self.db.add(sov)
        self.db.flush()
        self._recalculate_subcontract(sc)
        self.db.commit()
        self.db.refresh(sov)
        return sov

    def update_sov_line(
        self, line_id: int, data: SubcontractSOVLineUpdate
    ) -> Optional[SubcontractSOVLine]:
        sov = (
            self.db.query(SubcontractSOVLine)
            .join(Subcontract)
            .filter(
                SubcontractSOVLine.id == line_id,
                Subcontract.company_id == self.company_id,
            )
            .first()
        )
        if not sov:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(sov, key, value)

        sc = self.get_subcontract(sov.subcontract_id)
        if sc:
            self._calculate_sov_line(sov, sc.retainage_pct)
            self._recalculate_subcontract(sc)

        self.db.commit()
        self.db.refresh(sov)
        return sov

    def delete_sov_line(self, line_id: int) -> bool:
        sov = (
            self.db.query(SubcontractSOVLine)
            .join(Subcontract)
            .filter(
                SubcontractSOVLine.id == line_id,
                Subcontract.company_id == self.company_id,
            )
            .first()
        )
        if not sov:
            return False

        sc_id = sov.subcontract_id
        self.db.delete(sov)
        self.db.flush()

        sc = self.get_subcontract(sc_id)
        if sc:
            self._recalculate_subcontract(sc)

        self.db.commit()
        return True

    # -- Compliance Docs --

    def create_compliance_doc(
        self, data: ComplianceDocCreate
    ) -> Optional[SubcontractComplianceDoc]:
        sc = self.get_subcontract(data.subcontract_id)
        if not sc:
            return None

        doc = SubcontractComplianceDoc(
            subcontract_id=data.subcontract_id,
            company_id=self.company_id,
            doc_type=data.doc_type,
            status=data.status or "required",
            description=data.description,
            expiration_date=data.expiration_date,
            document_url=data.document_url,
            file_name=data.file_name,
            notes=data.notes,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def update_compliance_doc(
        self, doc_id: int, data: ComplianceDocUpdate
    ) -> Optional[SubcontractComplianceDoc]:
        doc = (
            self.db.query(SubcontractComplianceDoc)
            .join(Subcontract)
            .filter(
                SubcontractComplianceDoc.id == doc_id,
                Subcontract.company_id == self.company_id,
            )
            .first()
        )
        if not doc:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(doc, key, value)

        self.db.commit()
        self.db.refresh(doc)
        return doc

    def delete_compliance_doc(self, doc_id: int) -> bool:
        doc = (
            self.db.query(SubcontractComplianceDoc)
            .join(Subcontract)
            .filter(
                SubcontractComplianceDoc.id == doc_id,
                Subcontract.company_id == self.company_id,
            )
            .first()
        )
        if not doc:
            return False
        self.db.delete(doc)
        self.db.commit()
        return True

    # =========================================================================
    # VENDOR BILLS
    # =========================================================================

    def list_vendor_bills(
        self,
        page: int = 1,
        page_size: int = 20,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        record_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict:
        page_size = min(page_size, 200)
        query = self.db.query(VendorBill).filter(
            VendorBill.company_id == self.company_id,
            VendorBill.is_deleted == False,
        )

        if project_id:
            query = query.filter(VendorBill.project_id == project_id)
        if status:
            query = query.filter(VendorBill.status == status)
        if record_type:
            query = query.filter(VendorBill.record_type == record_type)
        if search:
            term = f"%{search}%"
            query = query.filter(
                (VendorBill.vendor_name.ilike(term))
                | (VendorBill.bill_number.ilike(term))
                | (VendorBill.sequence_name.ilike(term))
                | (VendorBill.vendor_invoice_ref.ilike(term))
            )

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(VendorBill.id.desc()).offset(skip).limit(page_size).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_vendor_bill(self, bill_id: int) -> Optional[VendorBill]:
        return (
            self.db.query(VendorBill)
            .filter(
                VendorBill.id == bill_id,
                VendorBill.company_id == self.company_id,
                VendorBill.is_deleted == False,
            )
            .first()
        )

    def get_vendor_bill_detail(self, bill_id: int) -> Optional[dict]:
        bill = self.get_vendor_bill(bill_id)
        if not bill:
            return None

        lines = sorted(bill.lines or [], key=lambda l: l.display_order)
        payments = bill.payments or []

        return {
            **{c.key: getattr(bill, c.key) for c in bill.__table__.columns},
            "lines": lines,
            "payments": payments,
            "line_count": len(lines),
            "payment_count": len(payments),
        }

    def create_vendor_bill(self, data: VendorBillCreate) -> VendorBill:
        bill = VendorBill(
            company_id=self.company_id,
            project_id=data.project_id,
            sequence_name=_next_sequence(self.db, VendorBill, self.company_id),
            bill_number=data.bill_number,
            vendor_name=data.vendor_name,
            vendor_contact=data.vendor_contact,
            record_type=data.record_type or "bill",
            status=data.status or "draft",
            bill_reference=data.bill_reference,
            description=data.description,
            issue_date=data.issue_date,
            due_date=data.due_date,
            tax_amount=data.tax_amount,
            payment_terms=data.payment_terms,
            purchase_order_id=data.purchase_order_id,
            subcontract_id=data.subcontract_id,
            vendor_invoice_ref=data.vendor_invoice_ref,
            notes=data.notes,
            created_by=self.user_id,
        )

        self.db.add(bill)
        self.db.flush()

        for line_data in data.lines or []:
            line = VendorBillLine(
                bill_id=bill.id,
                company_id=self.company_id,
                cost_code=line_data.cost_code,
                po_line_id=line_data.po_line_id,
                line_type=line_data.line_type,
                description=line_data.description,
                quantity=line_data.quantity,
                unit=line_data.unit,
                unit_cost=line_data.unit_cost,
                amount=line_data.amount or (line_data.quantity * line_data.unit_cost),
                display_order=line_data.display_order,
                notes=line_data.notes,
            )
            self.db.add(line)

        self.db.flush()
        self._recalculate_bill(bill)
        self.db.commit()
        self.db.refresh(bill)
        return bill

    def update_vendor_bill(
        self, bill_id: int, data: VendorBillUpdate
    ) -> Optional[VendorBill]:
        bill = self.get_vendor_bill(bill_id)
        if not bill:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(bill, key, value)
        bill.updated_by = self.user_id

        self._recalculate_bill(bill)
        self.db.commit()
        self.db.refresh(bill)
        return bill

    def delete_vendor_bill(self, bill_id: int) -> bool:
        bill = self.get_vendor_bill(bill_id)
        if not bill:
            return False
        self.db.delete(bill)
        self.db.commit()
        return True

    def approve_vendor_bill(self, bill_id: int) -> Optional[VendorBill]:
        bill = self.get_vendor_bill(bill_id)
        if not bill:
            return None

        from addons.agcm.services.approval_integration import submit_for_approval
        tasks = submit_for_approval(
            db=self.db,
            entity_type="vendor_bill",
            entity_id=bill.id,
            requester_id=self.user_id,
            company_id=self.company_id,
            amount=getattr(bill, "total_amount", None),
        )
        if tasks:
            bill.status = VendorBillStatus.PENDING_APPROVAL.value
            bill.updated_by = self.user_id
            self.db.commit()
            self.db.refresh(bill)
            return bill

        return self._finalize_vendor_bill_approval(bill)

    def _finalize_vendor_bill_approval(self, bill: VendorBill) -> VendorBill:
        bill.status = VendorBillStatus.APPROVED.value
        bill.approved_by = self.user_id
        bill.approved_date = date.today()
        bill.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(bill)
        return bill

    def record_payment(
        self, bill_id: int, data: VendorBillPaymentCreate
    ) -> Optional[VendorBillPayment]:
        """Record a payment against a vendor bill."""
        bill = self.get_vendor_bill(bill_id)
        if not bill:
            return None

        payment = VendorBillPayment(
            bill_id=bill_id,
            company_id=self.company_id,
            payment_date=data.payment_date,
            amount=data.amount,
            payment_method=data.payment_method,
            reference_number=data.reference_number,
            notes=data.notes,
            recorded_by=self.user_id,
        )
        self.db.add(payment)
        self.db.flush()

        # Update bill paid_amount and balance
        total_paid = (
            self.db.query(func.coalesce(func.sum(VendorBillPayment.amount), 0))
            .filter(VendorBillPayment.bill_id == bill_id)
            .scalar()
        )
        bill.paid_amount = float(total_paid)
        bill.balance_due = bill.total_amount - bill.paid_amount

        # Update status
        if bill.paid_amount >= bill.total_amount:
            bill.status = VendorBillStatus.PAID.value
        elif bill.paid_amount > 0:
            bill.status = VendorBillStatus.PARTIALLY_PAID.value

        bill.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def check_duplicate_bill(
        self,
        vendor_name: str,
        vendor_invoice_ref: Optional[str],
        project_id: int,
        exclude_id: Optional[int] = None,
    ) -> list:
        """Check for duplicate bills by vendor name + invoice reference."""
        if not vendor_invoice_ref:
            return []

        query = self.db.query(VendorBill).filter(
            VendorBill.company_id == self.company_id,
            VendorBill.project_id == project_id,
            VendorBill.vendor_name.ilike(f"%{vendor_name}%"),
            VendorBill.vendor_invoice_ref == vendor_invoice_ref,
        )

        if exclude_id:
            query = query.filter(VendorBill.id != exclude_id)

        return query.all()

    def auto_match_po(self, bill_id: int) -> Optional[dict]:
        """Try to match a bill to a PO by vendor name + approximate amount."""
        bill = self.get_vendor_bill(bill_id)
        if not bill:
            return None

        # Look for POs with same vendor and project
        pos = (
            self.db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.company_id == self.company_id,
                PurchaseOrder.project_id == bill.project_id,
                PurchaseOrder.vendor_name.ilike(f"%{bill.vendor_name}%"),
                PurchaseOrder.status.in_(["approved", "partially_received"]),
            )
            .all()
        )

        matches = []
        for po in pos:
            # Score based on amount similarity
            if po.total_amount > 0:
                diff_pct = (
                    abs(po.total_amount - bill.total_amount) / po.total_amount * 100
                )
            else:
                diff_pct = 100
            matches.append(
                {
                    "po_id": po.id,
                    "po_number": po.po_number,
                    "sequence_name": po.sequence_name,
                    "vendor_name": po.vendor_name,
                    "total_amount": po.total_amount,
                    "diff_pct": round(diff_pct, 1),
                }
            )

        matches.sort(key=lambda m: m["diff_pct"])
        return {"bill_id": bill_id, "matches": matches[:5]}

    def _recalculate_bill(self, bill: VendorBill):
        """Recalculate bill totals from lines."""
        lines = (
            self.db.query(VendorBillLine)
            .filter(VendorBillLine.bill_id == bill.id)
            .all()
        )
        subtotal = sum(l.amount for l in lines)
        bill.subtotal = subtotal
        bill.total_amount = subtotal + (bill.tax_amount or 0)
        bill.balance_due = bill.total_amount - (bill.paid_amount or 0)

    def recalculate_bill(self, bill_id: int) -> Optional[VendorBill]:
        bill = self.get_vendor_bill(bill_id)
        if not bill:
            return None
        self._recalculate_bill(bill)
        self.db.commit()
        self.db.refresh(bill)
        return bill

    # -- Bill Lines --

    def create_bill_line(
        self, data: VendorBillLineCreate, bill_id: int
    ) -> Optional[VendorBillLine]:
        bill = self.get_vendor_bill(bill_id)
        if not bill:
            return None

        line = VendorBillLine(
            bill_id=bill_id,
            company_id=self.company_id,
            cost_code=data.cost_code,
            po_line_id=data.po_line_id,
            line_type=data.line_type,
            description=data.description,
            quantity=data.quantity,
            unit=data.unit,
            unit_cost=data.unit_cost,
            amount=data.amount or (data.quantity * data.unit_cost),
            display_order=data.display_order,
            notes=data.notes,
        )
        self.db.add(line)
        self.db.flush()
        self._recalculate_bill(bill)
        self.db.commit()
        self.db.refresh(line)
        return line

    def update_bill_line(
        self, line_id: int, data: VendorBillLineUpdate
    ) -> Optional[VendorBillLine]:
        line = (
            self.db.query(VendorBillLine)
            .join(VendorBill)
            .filter(
                VendorBillLine.id == line_id,
                VendorBill.company_id == self.company_id,
            )
            .first()
        )
        if not line:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(line, key, value)

        bill = self.get_vendor_bill(line.bill_id)
        if bill:
            self._recalculate_bill(bill)

        self.db.commit()
        self.db.refresh(line)
        return line

    def delete_bill_line(self, line_id: int) -> bool:
        line = (
            self.db.query(VendorBillLine)
            .join(VendorBill)
            .filter(
                VendorBillLine.id == line_id,
                VendorBill.company_id == self.company_id,
            )
            .first()
        )
        if not line:
            return False

        bill_id = line.bill_id
        self.db.delete(line)
        self.db.flush()

        bill = self.get_vendor_bill(bill_id)
        if bill:
            self._recalculate_bill(bill)

        self.db.commit()
        return True
