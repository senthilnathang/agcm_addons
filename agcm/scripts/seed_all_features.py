"""
Comprehensive demo data seeder for all 10 architecture items.

Seeds: approval chains, tax rates, invoice/bill lines, vendors,
project members, module settings, and sample entities.

Usage:
    cd /opt/FastVue/backend
    source .venv/bin/activate
    ENV_FILE=.env.agcm python -c "from agcm_addons.agcm.scripts.seed_all_features import seed; seed()"
"""

import os
import sys
from datetime import date

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend"))
ADDONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if ADDONS_DIR not in sys.path:
    sys.path.insert(0, ADDONS_DIR)

os.environ.setdefault("ENV_FILE", ".env.agcm")

COMPANY_ID = 1
USER_ID = 1


def seed(db=None):
    close_db = False
    if db is None:
        from app.core.config import settings
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
        Session = sessionmaker(bind=engine)
        db = Session()
        close_db = True

    try:
        _seed_approval_chains(db)
        _seed_tax_rates(db)
        _seed_vendors(db)
        _seed_project_members(db)
        _seed_module_settings(db)
        print("\nAll feature demo data seeded successfully!")
    finally:
        if close_db:
            db.close()


def _seed_approval_chains(db):
    """Item #1: Approval chains for PO, CO, Subcontract."""
    print("\n=== Item #1: Approval Chains ===")
    from agcm.scripts.seed_approval_chains import seed as seed_chains
    seed_chains(db, COMPANY_ID, USER_ID)


def _seed_tax_rates(db):
    """Item #3: Tax rates for invoice/bill line items."""
    print("\n=== Item #3: Tax Rates ===")
    try:
        from addons.agcm_finance.models.tax_rate import TaxRate

        existing = db.query(TaxRate).filter(TaxRate.company_id == COMPANY_ID).count()
        if existing > 0:
            print(f"  Tax rates already exist ({existing}) — skipping")
            return

        rates = [
            TaxRate(company_id=COMPANY_ID, name="Sales Tax (8.25%)", rate=8.25, is_default=True),
            TaxRate(company_id=COMPANY_ID, name="Reduced Rate (5%)", rate=5.0),
            TaxRate(company_id=COMPANY_ID, name="GST (7%)", rate=7.0),
            TaxRate(company_id=COMPANY_ID, name="Tax Exempt", rate=0, is_active=True),
        ]
        for tr in rates:
            db.add(tr)
        db.commit()
        print(f"  Created {len(rates)} tax rates")
    except ImportError as e:
        print(f"  Skipped: {e}")


def _seed_vendors(db):
    """Item #6: Vendor/contact directory entries."""
    print("\n=== Item #6: Vendors ===")
    try:
        from addons.agcm_contact.models.vendor import Vendor

        existing = db.query(Vendor).filter(Vendor.company_id == COMPANY_ID).count()
        if existing > 0:
            print(f"  Vendors already exist ({existing}) — skipping")
            return

        vendors = [
            Vendor(company_id=COMPANY_ID, name="Durotech Inc", vendor_type="subcontractor",
                   contact_name="Mike Johnson", email="mike@durotech.com", phone="713-555-0101",
                   trade="Electrical", city="Houston", state="TX", payment_terms="Net 30"),
            Vendor(company_id=COMPANY_ID, name="Diversified Plastic Inc", vendor_type="supplier",
                   contact_name="Sarah Chen", email="sarah@divplastic.com", phone="713-555-0102",
                   trade="Materials", city="Dallas", state="TX", payment_terms="Net 45"),
            Vendor(company_id=COMPANY_ID, name="Gulf Coast Concrete", vendor_type="subcontractor",
                   contact_name="Tom Williams", email="tom@gcconcrete.com", phone="713-555-0103",
                   trade="Concrete", city="Houston", state="TX", payment_terms="Net 30"),
            Vendor(company_id=COMPANY_ID, name="Sterling Architecture", vendor_type="architect",
                   contact_name="Lisa Park", email="lisa@sterlingarch.com", phone="713-555-0104",
                   city="Houston", state="TX"),
            Vendor(company_id=COMPANY_ID, name="HCESD2 Administration", vendor_type="client",
                   contact_name="Robert Davis", email="rdavis@hcesd2.gov", phone="281-555-0105",
                   city="Humble", state="TX"),
            Vendor(company_id=COMPANY_ID, name="Southwest Steel Erectors", vendor_type="subcontractor",
                   contact_name="James Wilson", email="james@swsteel.com", phone="713-555-0106",
                   trade="Steel", city="Houston", state="TX", payment_terms="Net 30"),
            Vendor(company_id=COMPANY_ID, name="ProBuild Supply", vendor_type="supplier",
                   contact_name="Amy Brown", email="amy@probuild.com", phone="713-555-0107",
                   trade="General", city="Katy", state="TX", payment_terms="Net 15"),
            Vendor(company_id=COMPANY_ID, name="MEP Engineering Group", vendor_type="engineer",
                   contact_name="David Lee", email="david@mepeng.com", phone="713-555-0108",
                   city="Houston", state="TX"),
        ]
        for v in vendors:
            db.add(v)
        db.commit()
        print(f"  Created {len(vendors)} vendors")
    except ImportError as e:
        print(f"  Skipped: {e}")


def _seed_project_members(db):
    """Item #5: Project membership with roles."""
    print("\n=== Item #5: Project Members ===")
    try:
        from addons.agcm.models.project_member import ProjectMember
        from addons.agcm.models.project import Project

        existing = db.query(ProjectMember).filter(ProjectMember.company_id == COMPANY_ID).count()
        if existing > 0:
            print(f"  Project members already exist ({existing}) — skipping")
            return

        projects = db.query(Project).filter(
            Project.company_id == COMPANY_ID
        ).limit(5).all()

        if not projects:
            print("  No projects found — skipping member seeding")
            return

        for proj in projects:
            db.add(ProjectMember(
                project_id=proj.id, user_id=USER_ID, company_id=COMPANY_ID,
                role="owner", assigned_by=USER_ID,
            ))
        db.commit()
        print(f"  Created {len(projects)} project member records (owner role)")
    except ImportError as e:
        print(f"  Skipped: {e}")


def _seed_module_settings(db):
    """Item #10: Module-level settings."""
    print("\n=== Item #10: Module Settings ===")
    try:
        from addons.agcm.models.settings import AGCMSettings

        existing = db.query(AGCMSettings).filter(AGCMSettings.company_id == COMPANY_ID).count()
        if existing > 0:
            print(f"  Module settings already exist ({existing}) — skipping")
            return

        settings_data = [
            AGCMSettings(
                company_id=COMPANY_ID, module_name="finance",
                default_retention_pct=10.0, default_tax_rate_pct=8.25,
                default_payment_terms="Net 30", invoice_number_prefix="INV",
                currency_code="USD", created_by=USER_ID,
            ),
            AGCMSettings(
                company_id=COMPANY_ID, module_name="procurement",
                default_retention_pct=10.0, default_payment_terms="Net 30",
                po_number_prefix="PO", created_by=USER_ID,
            ),
            AGCMSettings(
                company_id=COMPANY_ID, module_name="estimate",
                default_markup_pct=15.0, default_tax_rate_pct=8.25,
                created_by=USER_ID,
            ),
            AGCMSettings(
                company_id=COMPANY_ID, module_name="schedule",
                working_hours_per_day=8.0, created_by=USER_ID,
            ),
            AGCMSettings(
                company_id=COMPANY_ID, module_name="resource",
                working_hours_per_day=8.0, overtime_multiplier=1.5,
                created_by=USER_ID,
            ),
        ]
        for s in settings_data:
            db.add(s)
        db.commit()
        print(f"  Created {len(settings_data)} module settings records")
    except ImportError as e:
        print(f"  Skipped: {e}")


if __name__ == "__main__":
    seed()
