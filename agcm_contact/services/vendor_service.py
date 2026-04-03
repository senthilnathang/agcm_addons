"""Vendor service — business logic for vendor/contact directory."""

import logging
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from addons.agcm_contact.models.vendor import Vendor, VendorType
from addons.agcm_contact.schemas.vendor import VendorCreate, VendorUpdate

logger = logging.getLogger(__name__)


class VendorService:
    def __init__(self, db: Session, company_id: int, user_id: int):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id

    def list_vendors(
        self,
        vendor_type: Optional[str] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = True,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        page_size = min(page_size, 200)
        q = self.db.query(Vendor).filter(Vendor.company_id == self.company_id)

        if vendor_type:
            q = q.filter(Vendor.vendor_type == vendor_type)
        if is_active is not None:
            q = q.filter(Vendor.is_active == is_active)
        if search:
            pattern = f"%{search}%"
            q = q.filter(
                Vendor.name.ilike(pattern)
                | Vendor.contact_name.ilike(pattern)
                | Vendor.email.ilike(pattern)
                | Vendor.trade.ilike(pattern)
            )

        total = q.count()
        items = (
            q.order_by(Vendor.name)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_vendor(self, vendor_id: int) -> Optional[Vendor]:
        return (
            self.db.query(Vendor)
            .filter(Vendor.id == vendor_id, Vendor.company_id == self.company_id)
            .first()
        )

    def create_vendor(self, data: VendorCreate) -> Vendor:
        vendor = Vendor(
            company_id=self.company_id,
            created_by=self.user_id,
            **data.model_dump(),
        )
        self.db.add(vendor)
        self.db.commit()
        self.db.refresh(vendor)
        return vendor

    def update_vendor(self, vendor_id: int, data: VendorUpdate) -> Optional[Vendor]:
        vendor = self.get_vendor(vendor_id)
        if not vendor:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(vendor, k, v)
        vendor.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(vendor)
        return vendor

    def delete_vendor(self, vendor_id: int) -> bool:
        vendor = self.get_vendor(vendor_id)
        if not vendor:
            return False
        self.db.delete(vendor)
        self.db.commit()
        return True

    def search_vendors(self, query: str, limit: int = 10) -> List[Vendor]:
        """Quick search for autocomplete — returns name + id."""
        pattern = f"%{query}%"
        return (
            self.db.query(Vendor)
            .filter(
                Vendor.company_id == self.company_id,
                Vendor.is_active == True,
                Vendor.name.ilike(pattern),
            )
            .order_by(Vendor.name)
            .limit(limit)
            .all()
        )
