"""
Tests for Vendor/Contact directory module.

Verifies:
- Vendor model CRUD
- Vendor type classification
- Search functionality
- Company scoping
"""

import uuid
from datetime import date

import pytest


def _uid():
    return uuid.uuid4().hex[:8]


class TestVendorModel:

    def test_create_vendor(self, db, company_id, load_model):
        Vendor = load_model("agcm_contact", "vendor", "Vendor")

        vendor = Vendor(
            company_id=company_id, name=f"ABC Electric {_uid()}",
            vendor_type="subcontractor", contact_name="John Smith",
            email="john@abc.com", phone="555-0100",
            trade="Electrical", payment_terms="Net 30",
        )
        db.add(vendor)
        db.flush()

        assert vendor.id is not None
        assert vendor.vendor_type == "subcontractor"
        assert vendor.is_active is True

    def test_vendor_types(self, db, company_id, load_model):
        Vendor = load_model("agcm_contact", "vendor", "Vendor")

        for vtype in ["vendor", "client", "subcontractor", "supplier", "architect", "engineer"]:
            v = Vendor(
                company_id=company_id, name=f"Test {vtype} {_uid()}",
                vendor_type=vtype,
            )
            db.add(v)
            db.flush()
            assert v.vendor_type == vtype

    def test_vendor_address(self, db, company_id, load_model):
        Vendor = load_model("agcm_contact", "vendor", "Vendor")

        vendor = Vendor(
            company_id=company_id, name=f"Full Address {_uid()}",
            vendor_type="vendor",
            address_line1="123 Main St", address_line2="Suite 200",
            city="Houston", state="TX", zip_code="77001", country="US",
        )
        db.add(vendor)
        db.flush()

        assert vendor.city == "Houston"
        assert vendor.state == "TX"

    def test_vendor_business_info(self, db, company_id, load_model):
        Vendor = load_model("agcm_contact", "vendor", "Vendor")

        vendor = Vendor(
            company_id=company_id, name=f"Biz Info {_uid()}",
            vendor_type="subcontractor",
            tax_id="12-3456789", license_number="LIC-001",
            website="https://example.com", payment_terms="Net 60",
        )
        db.add(vendor)
        db.flush()

        assert vendor.tax_id == "12-3456789"
        assert vendor.payment_terms == "Net 60"

    def test_company_scoping(self, db, company_id, load_model):
        """Vendors are scoped to company_id."""
        Vendor = load_model("agcm_contact", "vendor", "Vendor")

        v = Vendor(company_id=company_id, name=f"Scoped {_uid()}", vendor_type="vendor")
        db.add(v)
        db.flush()

        # Query with correct company
        found = db.query(Vendor).filter(
            Vendor.company_id == company_id, Vendor.id == v.id
        ).first()
        assert found is not None

        # Query with wrong company
        not_found = db.query(Vendor).filter(
            Vendor.company_id == 9999, Vendor.id == v.id
        ).first()
        assert not_found is None

    def test_search_by_name(self, db, company_id, load_model):
        Vendor = load_model("agcm_contact", "vendor", "Vendor")
        uid = _uid()

        db.add(Vendor(company_id=company_id, name=f"Durotech {uid}", vendor_type="vendor"))
        db.add(Vendor(company_id=company_id, name=f"Other Corp {uid}", vendor_type="vendor"))
        db.flush()

        results = db.query(Vendor).filter(
            Vendor.company_id == company_id,
            Vendor.name.ilike(f"%Durotech {uid}%"),
        ).all()
        assert len(results) == 1
        assert "Durotech" in results[0].name
