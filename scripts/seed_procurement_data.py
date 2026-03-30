"""Seed demo data for agcm_procurement module."""

import os
import sys
import random
import importlib.util
from datetime import date, timedelta

random.seed(55)

COMPANY_ID = 1
USER_ID = 1
PROJECT_IDS = list(range(1, 13))


def seed():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
    os.environ.setdefault("ENV_FILE", ".env.agcm")

    from app.core.config import settings
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    db = Session()

    addon = os.path.join(os.path.dirname(__file__), "..")

    def load_model(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod

    # Load base models
    for mf in ["lookups", "project", "daily_activity_log", "manpower", "weather", "notes",
                "inspection", "accident", "visitor", "safety_violation", "delay", "deficiency", "photo"]:
        load_model(f"_b_{mf}", os.path.join(addon, "agcm", "models", f"{mf}.py"))
    for mf in ["cost_catalog", "assembly", "estimate", "estimate_markup", "proposal", "takeoff"]:
        load_model(f"_e_{mf}", os.path.join(addon, "agcm_estimate", "models", f"{mf}.py"))
    try:
        from app.models import User, Company
    except Exception:
        pass

    mod_po = load_model("_p_po", os.path.join(addon, "agcm_procurement", "models", "purchase_order.py"))
    mod_sc = load_model("_p_sc", os.path.join(addon, "agcm_procurement", "models", "subcontract.py"))
    mod_vb = load_model("_p_vb", os.path.join(addon, "agcm_procurement", "models", "vendor_bill.py"))

    PurchaseOrder = mod_po.PurchaseOrder
    PurchaseOrderLine = mod_po.PurchaseOrderLine
    Subcontract = mod_sc.Subcontract
    SubcontractSOVLine = mod_sc.SubcontractSOVLine
    SubcontractComplianceDoc = mod_sc.SubcontractComplianceDoc
    VendorBill = mod_vb.VendorBill
    VendorBillLine = mod_vb.VendorBillLine
    VendorBillPayment = mod_vb.VendorBillPayment

    from app.db.base import Base
    Base.metadata.create_all(bind=engine, checkfirst=True)

    VENDORS = [
        "ABC Building Supply", "Texas Steel Co", "Gulf Coast Lumber", "Southwest Concrete",
        "Lone Star Equipment", "Premier Plumbing Supply", "Metro Electrical", "Capitol HVAC",
        "Bayou Paint Co", "Rio Grande Glass", "Alamo Fasteners", "Hill Country Roofing",
        "Dallas Door & Hardware", "Houston Fire Protection", "San Antonio Tile & Stone",
    ]

    PO_ITEMS = [
        ("Concrete 4000psi", "material", "cy", 135), ("Rebar #5 Grade 60", "material", "lf", 1.25),
        ("2x4 SPF Studs 8ft", "material", "ea", 4.50), ("1/2\" Drywall 4x8", "material", "ea", 12.50),
        ("Electrical Wire 12/2", "material", "lf", 0.85), ("PVC Pipe 4\" DWV", "material", "lf", 4.75),
        ("Roofing Shingles Bundle", "material", "ea", 35), ("Insulation R-19 Batt", "material", "sf", 1.10),
        ("Excavator 320 Rental", "equipment", "day", 2500), ("Crane 50T Rental", "equipment", "day", 3500),
        ("Concrete Pump Rental", "equipment", "day", 1800), ("Scissor Lift Rental", "equipment", "day", 350),
        ("Scaffolding System", "equipment", "day", 200), ("Compactor Rental", "equipment", "day", 450),
        ("Skilled Laborer", "labor", "hr", 45), ("Electrician Journeyman", "labor", "hr", 75),
    ]

    SC_SCOPES = [
        ("Electrical Rough-In", 120000, 280000), ("Plumbing Complete", 85000, 200000),
        ("HVAC Installation", 150000, 350000), ("Structural Steel Erection", 200000, 500000),
        ("Concrete Work", 100000, 300000), ("Roofing System", 80000, 180000),
        ("Fire Protection", 60000, 150000), ("Painting & Finishes", 40000, 120000),
        ("Site Utilities", 70000, 200000), ("Masonry Work", 50000, 150000),
    ]

    po_statuses = ["draft", "approved", "approved", "partially_received", "received"]
    sc_statuses = ["draft", "approved", "active", "active", "complete"]
    vb_statuses = ["draft", "pending_approval", "approved", "partially_paid", "paid", "paid"]
    record_types = ["bill", "bill", "bill", "bill", "expense", "vendor_credit"]
    pay_methods = ["check", "wire", "ach", "credit_card"]
    doc_types = ["insurance_coi", "workers_comp", "license", "w9", "bond", "safety_cert"]
    doc_statuses = ["submitted", "approved", "approved", "expired"]

    print("\n=== Seeding Procurement Data ===")

    # ---------------------------------------------------------------
    # Purchase Orders
    # ---------------------------------------------------------------
    po_count = 0
    po_line_count = 0
    po_ids_by_project = {}

    for pid in PROJECT_IDS:
        po_ids_by_project[pid] = []
        for i in range(5):
            po_count += 1
            status = random.choice(po_statuses)
            vendor = random.choice(VENDORS)
            po = PurchaseOrder(
                company_id=COMPANY_ID, project_id=pid,
                sequence_name=f"PO{po_count:05d}",
                po_number=f"PO-{pid:02d}-{i + 1:03d}",
                vendor_name=vendor, status=status,
                description=f"Purchase order for {vendor}",
                issue_date=date(2025, 2, 1) + timedelta(days=random.randint(0, 150)),
                expected_delivery=date(2025, 3, 1) + timedelta(days=random.randint(0, 90)),
                retainage_pct=random.choice([0, 0, 5, 10]),
                approved_by=USER_ID if status != "draft" else None,
                approved_date=date(2025, 3, 1) if status != "draft" else None,
                created_by=USER_ID,
            )
            db.add(po)
            db.flush()
            po_ids_by_project[pid].append(po.id)

            subtotal = 0
            num_lines = random.randint(3, 5)
            chosen_items = random.sample(PO_ITEMS, num_lines)
            for j, (desc, itype, unit, uc) in enumerate(chosen_items):
                po_line_count += 1
                qty = random.randint(5, 500) if itype == "material" else random.randint(1, 20)
                tc = round(qty * uc, 2)
                subtotal += tc
                rcv = round(qty * random.uniform(0.5, 1.0)) if status in ("partially_received", "received") else 0
                line = PurchaseOrderLine(
                    po_id=po.id, company_id=COMPANY_ID,
                    description=desc, item_type=itype,
                    quantity=qty, unit=unit, unit_cost=uc, total_cost=tc,
                    received_qty=rcv, display_order=j,
                )
                db.add(line)

            tax = round(subtotal * 0.0825, 2)
            po.subtotal = subtotal
            po.tax_amount = tax
            po.total_amount = round(subtotal + tax, 2)
            po.retainage_amount = round(po.total_amount * po.retainage_pct / 100, 2)

        db.commit()
    print(f"  Purchase Orders: {po_count}, Lines: {po_line_count}")

    # ---------------------------------------------------------------
    # Subcontracts
    # ---------------------------------------------------------------
    sc_count = 0
    sov_count = 0
    doc_count = 0

    for pid in PROJECT_IDS:
        for i in range(3):
            sc_count += 1
            scope_name, lo, hi = random.choice(SC_SCOPES)
            orig_amt = round(random.uniform(lo, hi), 2)
            co_amt = round(random.uniform(0, orig_amt * 0.15), 2) if random.random() < 0.4 else 0
            status = random.choice(sc_statuses)
            billed = round(orig_amt * random.uniform(0, 0.8), 2) if status in ("active", "complete") else 0
            paid = round(billed * random.uniform(0.5, 1.0), 2) if billed else 0

            sc = Subcontract(
                company_id=COMPANY_ID, project_id=pid,
                sequence_name=f"SC{sc_count:05d}",
                contract_number=f"SC-{pid:02d}-{i + 1:03d}",
                vendor_name=random.choice(VENDORS),
                status=status, scope_of_work=f"Complete {scope_name} per plans and specifications.",
                start_date=date(2025, 2, 1) + timedelta(days=random.randint(0, 60)),
                end_date=date(2025, 6, 1) + timedelta(days=random.randint(0, 120)),
                original_amount=orig_amt, approved_cos=co_amt,
                revised_amount=round(orig_amt + co_amt, 2),
                billed_to_date=billed, paid_to_date=paid,
                balance_remaining=round(orig_amt + co_amt - billed, 2),
                retainage_pct=random.choice([5, 10]),
                retainage_held=round(billed * 0.1, 2),
                approved_by=USER_ID if status != "draft" else None,
                created_by=USER_ID,
            )
            db.add(sc)
            db.flush()

            # SOV lines
            sov_names = [f"{scope_name} - Phase {j + 1}" for j in range(random.randint(4, 6))]
            remaining = orig_amt
            for j, sov_name in enumerate(sov_names):
                sov_count += 1
                is_last = j == len(sov_names) - 1
                val = remaining if is_last else round(remaining * random.uniform(0.15, 0.35), 2)
                remaining -= val
                prev = round(val * random.uniform(0, 0.5), 2) if billed else 0
                curr = round(val * random.uniform(0, 0.3), 2) if billed else 0
                stored = round(val * random.uniform(0, 0.1), 2) if billed else 0
                total_c = prev + curr + stored
                sov = SubcontractSOVLine(
                    subcontract_id=sc.id, company_id=COMPANY_ID,
                    description=sov_name, scheduled_value=val,
                    billed_previous=prev, billed_current=curr, stored_materials=stored,
                    total_completed=total_c,
                    pct_complete=round(total_c / val * 100, 1) if val else 0,
                    balance_to_finish=round(val - total_c, 2),
                    retainage=round(total_c * 0.1, 2),
                    display_order=j, source_type="original",
                )
                db.add(sov)

            # Compliance docs
            for dt in random.sample(doc_types, random.randint(2, 4)):
                doc_count += 1
                doc = SubcontractComplianceDoc(
                    subcontract_id=sc.id, company_id=COMPANY_ID,
                    doc_type=dt, status=random.choice(doc_statuses),
                    description=f"{dt.replace('_', ' ').title()} for {sc.vendor_name}",
                    expiration_date=date(2026, 1, 1) + timedelta(days=random.randint(0, 365)),
                    reviewed_by=USER_ID if random.random() < 0.6 else None,
                )
                db.add(doc)

        if pid % 4 == 0:
            db.commit()

    db.commit()
    print(f"  Subcontracts: {sc_count}, SOV Lines: {sov_count}, Compliance Docs: {doc_count}")

    # ---------------------------------------------------------------
    # Vendor Bills
    # ---------------------------------------------------------------
    vb_count = 0
    vbl_count = 0
    pay_count = 0

    for pid in PROJECT_IDS:
        po_ids = po_ids_by_project.get(pid, [])
        for i in range(5):
            vb_count += 1
            status = random.choice(vb_statuses)
            rt = random.choice(record_types)
            amt = round(random.uniform(1000, 80000), 2)
            tax = round(amt * 0.0825, 2) if rt == "bill" else 0
            total = round(amt + tax, 2)
            paid = total if status == "paid" else (round(total * random.uniform(0.3, 0.7), 2) if status == "partially_paid" else 0)

            vb = VendorBill(
                company_id=COMPANY_ID, project_id=pid,
                sequence_name=f"VB{vb_count:05d}",
                bill_number=f"VB-{pid:02d}-{i + 1:03d}",
                vendor_name=random.choice(VENDORS),
                record_type=rt, status=status,
                vendor_invoice_ref=f"VINV-{random.randint(10000, 99999)}",
                issue_date=date(2025, 2, 15) + timedelta(days=random.randint(0, 120)),
                due_date=date(2025, 3, 15) + timedelta(days=random.randint(0, 60)),
                subtotal=amt, tax_amount=tax, total_amount=total,
                paid_amount=paid, balance_due=round(total - paid, 2),
                payment_terms=random.choice(["Net 30", "Net 45", "Net 60", "Due on Receipt"]),
                purchase_order_id=random.choice(po_ids) if po_ids and random.random() < 0.4 else None,
                duplicate_flag=(random.random() < 0.08),
                created_by=USER_ID,
            )
            db.add(vb)
            db.flush()

            # Lines
            for j in range(random.randint(2, 4)):
                vbl_count += 1
                qty = round(random.uniform(1, 200), 1)
                uc = round(random.uniform(10, 2000), 2)
                line = VendorBillLine(
                    bill_id=vb.id, company_id=COMPANY_ID,
                    description=f"Bill line item #{j + 1}",
                    line_type=random.choice(["material", "labor", "equipment", "other"]),
                    quantity=qty, unit=random.choice(["ea", "lf", "sf", "hr", "day"]),
                    unit_cost=uc, amount=round(qty * uc, 2),
                    display_order=j,
                )
                db.add(line)

            # Payments
            if status in ("partially_paid", "paid"):
                num_payments = 2 if status == "paid" and total > 20000 else 1
                pay_remaining = paid
                for k in range(num_payments):
                    pay_count += 1
                    pay_amt = pay_remaining if k == num_payments - 1 else round(pay_remaining * 0.6, 2)
                    pay_remaining -= pay_amt
                    payment = VendorBillPayment(
                        bill_id=vb.id, company_id=COMPANY_ID,
                        payment_date=date(2025, 4, 1) + timedelta(days=random.randint(0, 60) + k * 15),
                        amount=pay_amt,
                        payment_method=random.choice(pay_methods),
                        reference_number=f"CHK-{random.randint(10000, 99999)}",
                        recorded_by=USER_ID,
                    )
                    db.add(payment)

        if pid % 3 == 0:
            db.commit()

    db.commit()
    print(f"  Vendor Bills: {vb_count}, Lines: {vbl_count}, Payments: {pay_count}")

    # Summary
    from sqlalchemy import text
    tables = [
        "agcm_purchase_orders", "agcm_purchase_order_lines",
        "agcm_subcontracts", "agcm_subcontract_sov_lines", "agcm_subcontract_compliance",
        "agcm_vendor_bills", "agcm_vendor_bill_lines", "agcm_vendor_bill_payments",
    ]
    total = 0
    print(f"\n{'=' * 55}")
    print("PROCUREMENT SEED SUMMARY")
    print(f"{'=' * 55}")
    for t in tables:
        c = db.execute(text(f"SELECT count(*) FROM {t}")).scalar()
        total += c
        print(f"  {t:42s} {c:>6}")
    print(f"  {'─' * 49}")
    print(f"  {'TOTAL':42s} {total:>6}")
    print(f"{'=' * 55}")

    db.close()
    print("Done!")


if __name__ == "__main__":
    seed()
