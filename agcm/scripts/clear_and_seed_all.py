"""
Clear all AGCM demo data and re-seed everything from scratch.

Truncates all agcm_* tables (preserving schema) then seeds:
- Base AGCM data (projects, daily logs, weather, trades, photos)
- All 15 module demo data
- New feature data (approval chains, tax rates, vendors, project members, settings)

Usage:
    cd /opt/FastVue/backend
    source .venv/bin/activate
    ENV_FILE=.env.agcm python -m agcm_addons.agcm.scripts.clear_and_seed_all
"""

import os
import sys
import random
from datetime import date, datetime, timedelta

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend"))
ADDONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if ADDONS_DIR not in sys.path:
    sys.path.insert(0, ADDONS_DIR)

os.environ.setdefault("ENV_FILE", ".env.agcm")

from app.core.config import settings
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)

COMPANY_ID = 1
USER_ID = 1


def clear_all_agcm_data(db):
    """Truncate all agcm_* tables."""
    print("=" * 60)
    print("CLEARING ALL AGCM DATA")
    print("=" * 60)

    # Get all agcm tables
    result = db.execute(text(
        "SELECT tablename FROM pg_tables WHERE tablename LIKE 'agcm_%' ORDER BY tablename"
    ))
    tables = [row[0] for row in result]
    print(f"Found {len(tables)} agcm tables")

    # Truncate all in one statement with CASCADE
    if tables:
        table_list = ", ".join(f'"{t}"' for t in tables)
        db.execute(text(f"TRUNCATE {table_list} CASCADE"))
        db.commit()
        print(f"Truncated {len(tables)} tables")


def seed_lookups(db):
    """Seed lookup/settings data: trades, types, etc."""
    print("\n--- Seeding lookups ---")

    trades = [
        "General Contractor", "Electrical", "Plumbing", "HVAC",
        "Concrete", "Steel", "Drywall", "Painting", "Roofing",
        "Flooring", "Carpentry", "Masonry", "Landscaping", "Fire Protection",
    ]
    for t in trades:
        db.execute(text(
            "INSERT INTO agcm_trades (company_id, name) VALUES (:cid, :name)"
        ), {"cid": COMPANY_ID, "name": t})

    for tbl, items in [
        ("agcm_inspection_types", ["Foundation", "Framing", "Electrical Rough-In", "Plumbing Rough-In", "Final"]),
        ("agcm_accident_types", ["Fall", "Struck By", "Caught Between", "Electrical", "Vehicle"]),
        ("agcm_violation_types", ["PPE Missing", "Fall Protection", "Housekeeping", "Excavation", "Scaffolding"]),
    ]:
        for item in items:
            db.execute(text(f"INSERT INTO {tbl} (company_id, name) VALUES (:cid, :name)"),
                       {"cid": COMPANY_ID, "name": item})

    db.commit()
    print(f"  Trades: {len(trades)}, Types: 15")


def seed_projects(db):
    """Seed construction projects."""
    print("\n--- Seeding projects ---")
    projects = [
        ("HCESD2 Admin Building", "PRJ-2024-001", "14418 Beaumont Hwy", "Houston", "TX"),
        ("Northshore Medical Center", "PRJ-2024-002", "2500 Kingwood Dr", "Kingwood", "TX"),
        ("Heritage Plaza Renovation", "PRJ-2024-003", "1111 Bagby St", "Houston", "TX"),
        ("Westchase Office Park", "PRJ-2024-004", "9801 Westheimer Rd", "Houston", "TX"),
        ("Cypress Creek Apartments", "PRJ-2024-005", "7700 Louetta Rd", "Spring", "TX"),
        ("Memorial Park Pavilion", "PRJ-2024-006", "6501 Memorial Dr", "Houston", "TX"),
        ("Pearland Town Center Phase 3", "PRJ-2024-007", "11200 Broadway", "Pearland", "TX"),
        ("Sugar Land Innovation Hub", "PRJ-2024-008", "15400 SW Freeway", "Sugar Land", "TX"),
    ]
    project_ids = []
    for name, ref, addr, city, state in projects:
        result = db.execute(text(
            "INSERT INTO agcm_projects (company_id, name, ref_number, street, city, state, "
            "start_date, end_date, status, owner_id, created_by) "
            "VALUES (:cid, :name, :ref, :addr, :city, :state, :start, :end, 'NEW', :uid, :uid) "
            "RETURNING id"
        ), {
            "cid": COMPANY_ID, "name": name, "ref": ref, "addr": addr,
            "city": city, "state": state, "uid": USER_ID,
            "start": date(2024, 1, 15), "end": date(2025, 12, 31),
        })
        project_ids.append(result.fetchone()[0])

    db.commit()
    print(f"  Created {len(project_ids)} projects")
    return project_ids


def seed_cost_codes(db, project_ids):
    """Seed cost codes for projects."""
    print("\n--- Seeding cost codes ---")
    codes = [
        ("01-000", "General Requirements"), ("02-000", "Sitework"),
        ("03-000", "Concrete"), ("04-000", "Masonry"),
        ("05-000", "Metals"), ("06-000", "Wood & Plastics"),
        ("07-000", "Thermal & Moisture"), ("08-000", "Doors & Windows"),
        ("09-000", "Finishes"), ("10-000", "Specialties"),
        ("15-000", "Mechanical"), ("16-000", "Electrical"),
    ]
    count = 0
    for pid in project_ids[:4]:
        for code, name in codes:
            db.execute(text(
                "INSERT INTO agcm_cost_codes (company_id, project_id, code, name, category) "
                "VALUES (:cid, :pid, :code, :name, :cat)"
            ), {"cid": COMPANY_ID, "pid": pid, "code": code, "name": name, "cat": "CSI"})
            count += 1
    db.commit()
    print(f"  Created {count} cost codes")


def seed_budgets(db, project_ids):
    """Seed budget lines for projects."""
    print("\n--- Seeding budgets ---")
    count = 0
    for pid in project_ids[:4]:
        for desc, planned, committed, actual in [
            ("General Requirements", 150000, 120000, 80000),
            ("Sitework", 200000, 180000, 100000),
            ("Concrete", 350000, 320000, 200000),
            ("Metals", 280000, 250000, 150000),
            ("Mechanical", 400000, 350000, 180000),
            ("Electrical", 320000, 290000, 160000),
            ("Approved Change Orders", 0, 45000, 0),
            ("Purchase Orders", 0, 180000, 0),
            ("Subcontracts", 0, 520000, 0),
            ("Vendor Bills", 0, 0, 120000),
            ("Labor (Timesheets)", 0, 0, 95000),
        ]:
            db.execute(text(
                "INSERT INTO agcm_budgets (company_id, project_id, description, "
                "planned_amount, committed_amount, actual_amount, created_by) "
                "VALUES (:cid, :pid, :desc, :planned, :committed, :actual, :uid)"
            ), {"cid": COMPANY_ID, "pid": pid, "desc": desc,
                "planned": planned, "committed": committed, "actual": actual, "uid": USER_ID})
            count += 1
    db.commit()
    print(f"  Created {count} budget lines")


def seed_rfis(db, project_ids):
    """Seed RFIs."""
    print("\n--- Seeding RFIs ---")
    rfis = [
        ("Steel connection detail clarification", "open", 5000, 3),
        ("Foundation depth change request", "answered", 15000, 7),
        ("Window specification update", "open", 0, 0),
        ("HVAC duct routing conflict", "in_progress", 8000, 5),
        ("Elevator shaft dimension discrepancy", "closed", 25000, 14),
        ("Fire sprinkler head spacing", "open", 0, 0),
        ("Parking lot grading revision", "answered", 12000, 10),
        ("Exterior cladding material substitution", "draft", 50000, 21),
    ]
    count = 0
    for pid in project_ids[:4]:
        for i, (subject, status, cost, days) in enumerate(rfis):
            db.execute(text(
                "INSERT INTO agcm_rfis (company_id, project_id, sequence_name, subject, "
                "status, cost_impact, schedule_impact_days, priority, created_by, "
                "is_deleted) "
                "VALUES (:cid, :pid, :seq, :subject, :status, :cost, :days, :priority, :uid, false)"
            ), {"cid": COMPANY_ID, "pid": pid, "seq": f"RFI{(pid*100+i+1):05d}",
                "subject": subject, "status": status, "cost": cost, "days": days,
                "priority": random.choice(["low", "medium", "high"]), "uid": USER_ID})
            count += 1
    db.commit()
    print(f"  Created {count} RFIs")


def seed_change_orders(db, project_ids):
    """Seed change orders."""
    print("\n--- Seeding change orders ---")
    cos = [
        ("Foundation redesign", 45000, 14, "approved"),
        ("Additional steel bracing", 22000, 7, "approved"),
        ("Owner-requested finish upgrade", 35000, 10, "pending"),
        ("Unforeseen soil condition", 18000, 5, "draft"),
        ("Electrical panel relocation", 8500, 3, "approved"),
    ]
    count = 0
    for pid in project_ids[:4]:
        for i, (title, cost, days, status) in enumerate(cos):
            db.execute(text(
                "INSERT INTO agcm_change_orders (company_id, project_id, sequence_name, "
                "title, status, cost_impact, schedule_impact_days, created_by, "
                "is_deleted) "
                "VALUES (:cid, :pid, :seq, :title, :status, :cost, :days, :uid, false)"
            ), {"cid": COMPANY_ID, "pid": pid, "seq": f"CO{(pid*100+i+1):05d}",
                "title": title, "status": status, "cost": cost, "days": days, "uid": USER_ID})
            count += 1
    db.commit()
    print(f"  Created {count} change orders")


def seed_submittals(db, project_ids):
    """Seed submittals."""
    print("\n--- Seeding submittals ---")
    subs = [
        ("Concrete mix design", "Samples", "approved", "high"),
        ("Steel shop drawings", "Shop Drawings", "in_review", "urgent"),
        ("HVAC equipment cut sheets", "Certificates", "draft", "medium"),
        ("Roofing material samples", "Samples", "pending_review", "low"),
        ("Fire sprinkler shop drawings", "Shop Drawings", "approved", "high"),
        ("Window frame specifications", "Design Data", "rejected", "medium"),
    ]
    count = 0
    for pid in project_ids[:4]:
        for i, (title, stype, status, priority) in enumerate(subs):
            db.execute(text(
                "INSERT INTO agcm_submittals (company_id, project_id, sequence_name, "
                "title, status, priority, revision, created_by) "
                "VALUES (:cid, :pid, :seq, :title, :status, :pri, 1, :uid)"
            ), {"cid": COMPANY_ID, "pid": pid, "seq": f"SUB{(pid*100+i+1):05d}",
                "title": title, "status": status, "pri": priority, "uid": USER_ID})
            count += 1
    db.commit()
    print(f"  Created {count} submittals")


def seed_purchase_orders(db, project_ids):
    """Seed purchase orders."""
    print("\n--- Seeding purchase orders ---")
    pos = [
        ("Rebar Supply", "Durotech Inc", 125000, "approved"),
        ("Concrete Delivery", "Gulf Coast Concrete", 85000, "approved"),
        ("Steel Joists", "Southwest Steel", 210000, "pending_approval"),
        ("Drywall Materials", "ProBuild Supply", 45000, "draft"),
        ("Electrical Fixtures", "Diversified Plastic", 67000, "approved"),
    ]
    count = 0
    for pid in project_ids[:4]:
        for i, (desc, vendor, amount, status) in enumerate(pos):
            db.execute(text(
                "INSERT INTO agcm_purchase_orders (company_id, project_id, sequence_name, "
                "po_number, vendor_name, status, subtotal, tax_amount, total_amount, "
                "retainage_pct, retainage_amount, created_by, is_deleted) "
                "VALUES (:cid, :pid, :seq, :po, :vendor, :status, :amt, 0, :amt, "
                "0, 0, :uid, false)"
            ), {"cid": COMPANY_ID, "pid": pid, "seq": f"PO{(pid*100+i+1):05d}",
                "po": f"PO-{pid}-{i+1:03d}", "vendor": vendor,
                "status": status, "amt": amount, "uid": USER_ID})
            count += 1
    db.commit()
    print(f"  Created {count} purchase orders")


def seed_invoices_and_bills(db, project_ids):
    """Seed invoices and bills with line items."""
    print("\n--- Seeding invoices, bills, tax rates ---")

    # Tax rates
    for name, rate, default in [
        ("Sales Tax (8.25%)", 8.25, True), ("Reduced (5%)", 5.0, False),
        ("GST (7%)", 7.0, False), ("Tax Exempt", 0, False),
    ]:
        db.execute(text(
            "INSERT INTO agcm_tax_rates (company_id, name, rate, is_default, is_active, is_compound) "
            "VALUES (:cid, :name, :rate, :default, true, false)"
        ), {"cid": COMPANY_ID, "name": name, "rate": rate, "default": default})

    inv_count = 0
    bill_count = 0
    for pid in project_ids[:4]:
        # Invoices
        for i, (client, amount, status) in enumerate([
            ("HCESD2 Administration", 150000, "sent"),
            ("Northshore Development LLC", 85000, "draft"),
            ("Heritage Properties", 220000, "paid"),
        ]):
            db.execute(text(
                "INSERT INTO agcm_invoices (company_id, project_id, sequence_name, "
                "invoice_number, client_name, status, amount, tax_amount, total_amount, "
                "paid_amount, balance_due, issue_date, due_date, created_by) "
                "VALUES (:cid, :pid, :seq, :inv, :client, :status, :amt, :tax, :total, "
                ":paid, :balance, :issue, :due, :uid)"
            ), {"cid": COMPANY_ID, "pid": pid, "seq": f"INV{(pid*100+i+1):05d}",
                "inv": f"INV-{pid}-{i+1:03d}", "client": client, "status": status,
                "amt": amount, "tax": round(amount * 0.0825, 2),
                "total": round(amount * 1.0825, 2),
                "paid": round(amount * 1.0825, 2) if status == "paid" else 0,
                "balance": round(amount * 1.0825, 2) if status != "paid" else 0,
                "issue": date(2025, 1 + i, 1), "due": date(2025, 2 + i, 1),
                "uid": USER_ID})
            inv_count += 1

        # Bills
        for i, (vendor, amount, status) in enumerate([
            ("Durotech Inc", 45000, "approved"),
            ("ProBuild Supply", 22000, "draft"),
            ("Gulf Coast Concrete", 67000, "paid"),
        ]):
            db.execute(text(
                "INSERT INTO agcm_bills (company_id, project_id, sequence_name, "
                "bill_number, vendor_name, status, amount, tax_amount, total_amount, "
                "paid_amount, balance_due, issue_date, due_date, created_by) "
                "VALUES (:cid, :pid, :seq, :bill, :vendor, :status, :amt, :tax, :total, "
                ":paid, :balance, :issue, :due, :uid)"
            ), {"cid": COMPANY_ID, "pid": pid, "seq": f"BILL{(pid*100+i+1):05d}",
                "bill": f"BILL-{pid}-{i+1:03d}", "vendor": vendor, "status": status,
                "amt": amount, "tax": round(amount * 0.0825, 2),
                "total": round(amount * 1.0825, 2),
                "paid": round(amount * 1.0825, 2) if status == "paid" else 0,
                "balance": 0 if status == "paid" else round(amount * 1.0825, 2),
                "issue": date(2025, 1 + i, 15), "due": date(2025, 2 + i, 15),
                "uid": USER_ID})
            bill_count += 1

    db.commit()
    print(f"  Invoices: {inv_count}, Bills: {bill_count}, Tax rates: 4")


def seed_vendors(db):
    """Seed vendor directory."""
    print("\n--- Seeding vendors ---")
    vendors = [
        ("Durotech Inc", "subcontractor", "Mike Johnson", "mike@durotech.com", "Electrical", "Houston", "TX"),
        ("Diversified Plastic Inc", "supplier", "Sarah Chen", "sarah@divplastic.com", "Materials", "Dallas", "TX"),
        ("Gulf Coast Concrete", "subcontractor", "Tom Williams", "tom@gcconcrete.com", "Concrete", "Houston", "TX"),
        ("Sterling Architecture", "architect", "Lisa Park", "lisa@sterlingarch.com", None, "Houston", "TX"),
        ("HCESD2 Administration", "client", "Robert Davis", "rdavis@hcesd2.gov", None, "Humble", "TX"),
        ("Southwest Steel Erectors", "subcontractor", "James Wilson", "james@swsteel.com", "Steel", "Houston", "TX"),
        ("ProBuild Supply", "supplier", "Amy Brown", "amy@probuild.com", "General", "Katy", "TX"),
        ("MEP Engineering Group", "engineer", "David Lee", "david@mepeng.com", None, "Houston", "TX"),
        ("ABC Plumbing Co", "subcontractor", "Bill Taylor", "bill@abcplumb.com", "Plumbing", "Houston", "TX"),
        ("Lone Star Roofing", "subcontractor", "Carlos Garcia", "carlos@lsroofing.com", "Roofing", "Houston", "TX"),
        ("Texas Fire Protection", "subcontractor", "Nancy White", "nancy@txfire.com", "Fire Protection", "Houston", "TX"),
        ("Bayou City HVAC", "subcontractor", "Kevin Moore", "kevin@baycityhvac.com", "HVAC", "Houston", "TX"),
    ]
    for name, vtype, contact, email, trade, city, state in vendors:
        db.execute(text(
            "INSERT INTO agcm_vendors (company_id, name, vendor_type, contact_name, email, "
            "trade, city, state, payment_terms, is_active) "
            "VALUES (:cid, :name, :vtype, :contact, :email, :trade, :city, :state, 'Net 30', true)"
        ), {"cid": COMPANY_ID, "name": name, "vtype": vtype, "contact": contact,
            "email": email, "trade": trade, "city": city, "state": state})
    db.commit()
    print(f"  Created {len(vendors)} vendors")


def seed_project_members(db, project_ids):
    """Seed project membership with roles."""
    print("\n--- Seeding project members ---")
    count = 0
    for pid in project_ids:
        db.execute(text(
            "INSERT INTO agcm_project_members (project_id, user_id, company_id, role, is_active) "
            "VALUES (:pid, :uid, :cid, 'owner', true)"
        ), {"pid": pid, "uid": USER_ID, "cid": COMPANY_ID})
        count += 1
    db.commit()
    print(f"  Created {count} project members")


def seed_module_settings(db):
    """Seed module-level settings."""
    print("\n--- Seeding module settings ---")
    settings_data = [
        ("finance", 10.0, 0, 8.25, "Net 30", "PO", "INV", "USD", 8.0, 1.5),
        ("procurement", 10.0, 0, 0, "Net 30", "PO", "INV", "USD", 8.0, 1.5),
        ("estimate", 0, 15.0, 8.25, "Net 30", "PO", "INV", "USD", 8.0, 1.5),
        ("schedule", 0, 0, 0, "Net 30", "PO", "INV", "USD", 8.0, 1.5),
        ("resource", 0, 0, 0, "Net 30", "PO", "INV", "USD", 8.0, 1.5),
    ]
    for mod, ret, markup, tax, terms, po_pfx, inv_pfx, curr, hours, ot in settings_data:
        db.execute(text(
            "INSERT INTO agcm_settings (company_id, module_name, default_retention_pct, "
            "default_markup_pct, default_tax_rate_pct, default_payment_terms, "
            "po_number_prefix, invoice_number_prefix, currency_code, "
            "working_hours_per_day, overtime_multiplier, settings_json, created_by) "
            "VALUES (:cid, :mod, :ret, :markup, :tax, :terms, :po, :inv, :curr, :hrs, :ot, '{}', :uid)"
        ), {"cid": COMPANY_ID, "mod": mod, "ret": ret, "markup": markup, "tax": tax,
            "terms": terms, "po": po_pfx, "inv": inv_pfx, "curr": curr,
            "hrs": hours, "ot": ot, "uid": USER_ID})
    db.commit()
    print(f"  Created {len(settings_data)} module settings")


def seed_daily_log_data(db, project_ids):
    """Seed daily logs, weather, manpower, notes, inspections, visitors,
    safety violations, delays, deficiencies, accidents — from original seed_demo_data."""
    print("\n--- Seeding daily log data (daily logs, weather, manpower, etc.) ---")

    MANPOWER_COMMENTS = [
        "Concrete pouring crew", "Electrical rough-in", "Plumbing installation",
        "HVAC ductwork", "Structural steel erection", "Drywall hanging",
        "Exterior painting", "Landscaping crew", "Fire sprinkler installation",
    ]
    NOTES_COMMENTS = [
        "Site and Landscaping", "Electrical and Low Voltage", "Plumbing and Restrooms",
        "Mechanical", "Roofing", "Concrete Work", "Steel Erection", "Flooring",
    ]
    NOTES_DESCRIPTIONS = [
        "Trenching for landscaping irrigation lines", "Final wiring for power",
        "Restroom trim out beginning today", "No work observed",
        "Concrete pour scheduled for tomorrow", "Steel delivery arrived on site",
        "Tile installation in lobby area", "Interior painting continues",
    ]
    LOCATIONS = [
        "Floor 1", "Floor 2", "Floor 3", "Basement", "Lobby",
        "Exterior North", "Exterior South", "Parking Garage", "Roof",
        "Mechanical Room", "Loading Dock",
    ]
    VISITOR_NAMES = [
        "John Smith", "Maria Garcia", "David Johnson", "Sarah Williams",
        "Michael Brown", "Jennifer Davis", "Robert Miller",
    ]
    VISITOR_REASONS = [
        "Site inspection", "Material delivery", "Client walkthrough",
        "Engineering review", "Safety audit", "City inspector visit",
    ]
    DELAY_REASONS = [
        "Weather delay - heavy rain", "Material delivery delayed",
        "Equipment breakdown", "Permit not yet approved",
        "Design change requested", "Subcontractor no-show",
    ]
    DEFICIENCY_NAMES = [
        "Concrete crack in foundation", "Misaligned door frame",
        "Paint finish defect", "Plumbing leak at joint",
        "Electrical outlet not grounded", "Window seal incomplete",
    ]
    SAFETY_DESCRIPTIONS = [
        "Worker without hard hat", "Missing guardrail on scaffold",
        "Electrical cord in walkway", "Unsecured ladder",
        "No safety glasses worn", "Blocked emergency exit",
    ]

    log_counter = 0
    log_ids = []
    for pid in project_ids:
        base_date = date(2025, 6, 1)
        for d in range(30):  # 30 days per project
            log_date = base_date + timedelta(days=d)
            if log_date.weekday() >= 5:
                continue
            log_counter += 1
            result = db.execute(text(
                "INSERT INTO agcm_daily_activity_logs (company_id, sequence_name, date, "
                "project_id, created_by) "
                "VALUES (:cid, :seq, :date, :pid, :uid) RETURNING id"
            ), {"cid": COMPANY_ID, "seq": f"DL{log_counter:05d}",
                "date": log_date, "pid": pid, "uid": USER_ID})
            log_id = result.fetchone()[0]
            log_ids.append((log_id, pid, log_date))
    db.commit()
    print(f"  Daily Logs: {len(log_ids)}")

    # Manpower (2 per log)
    mp_count = 0
    for log_id, pid, log_date in log_ids:
        for _ in range(2):
            mp_count += 1
            workers = random.randint(2, 12)
            hours = random.choice([6.0, 8.0, 10.0])
            db.execute(text(
                "INSERT INTO agcm_manpower (company_id, sequence_name, name, location, "
                "number_of_workers, number_of_hours, total_hours, dailylog_id, project_id, created_by) "
                "VALUES (:cid, :seq, :name, :loc, :workers, :hours, :total, :log, :pid, :uid)"
            ), {"cid": COMPANY_ID, "seq": f"MP{mp_count:05d}",
                "name": random.choice(MANPOWER_COMMENTS), "loc": random.choice(LOCATIONS),
                "workers": workers, "hours": hours, "total": workers * hours,
                "log": log_id, "pid": pid, "uid": USER_ID})
    db.commit()
    print(f"  Manpower: {mp_count}")

    # Notes (1 per log)
    note_count = 0
    for log_id, pid, log_date in log_ids:
        note_count += 1
        db.execute(text(
            "INSERT INTO agcm_notes (company_id, sequence_name, name, description, "
            "location, dailylog_id, project_id, created_by) "
            "VALUES (:cid, :seq, :name, :desc, :loc, :log, :pid, :uid)"
        ), {"cid": COMPANY_ID, "seq": f"N{note_count:05d}",
            "name": random.choice(NOTES_COMMENTS), "desc": random.choice(NOTES_DESCRIPTIONS),
            "loc": random.choice(LOCATIONS), "log": log_id, "pid": pid, "uid": USER_ID})
    db.commit()
    print(f"  Notes: {note_count}")

    # Visitors (every log, 1-2 per log → ~25-40 per project)
    vis_count = 0
    for log_id, pid, log_date in log_ids:
        for _ in range(random.randint(1, 2)):
            vis_count += 1
            entry_hour = random.randint(7, 14)
            db.execute(text(
                "INSERT INTO agcm_visitors (company_id, sequence_name, name, reason, "
                "visit_entry_time, visit_exit_time, "
                "dailylog_id, project_id, created_by) "
                "VALUES (:cid, :seq, :name, :reason, :entry, :exit, :log, :pid, :uid)"
            ), {"cid": COMPANY_ID, "seq": f"V{vis_count:05d}",
                "name": random.choice(VISITOR_NAMES), "reason": random.choice(VISITOR_REASONS),
                "entry": datetime.combine(log_date, datetime.min.time()).replace(hour=entry_hour),
                "exit": datetime.combine(log_date, datetime.min.time()).replace(hour=entry_hour + 2),
                "log": log_id, "pid": pid, "uid": USER_ID})
    db.commit()
    print(f"  Visitors: {vis_count}")

    # Inspections (every log, 1-2 per log → ~25-40 per project)
    insp_count = 0
    insp_type_ids = [r[0] for r in db.execute(text(
        "SELECT id FROM agcm_inspection_types WHERE company_id = :cid"
    ), {"cid": COMPANY_ID}).fetchall()]
    if insp_type_ids:
        for log_id, pid, log_date in log_ids:
            for _ in range(random.randint(1, 2)):
                insp_count += 1
                db.execute(text(
                    "INSERT INTO agcm_inspections (company_id, sequence_name, name, "
                    "inspection_type_id, result, dailylog_id, project_id, created_by) "
                    "VALUES (:cid, :seq, :name, :tid, :result, :log, :pid, :uid)"
                ), {"cid": COMPANY_ID, "seq": f"I{insp_count:05d}",
                    "name": f"Inspection #{insp_count}",
                    "tid": random.choice(insp_type_ids),
                    "result": random.choice(["Pass", "Pass", "Fail", "Conditional Pass"]),
                    "log": log_id, "pid": pid, "uid": USER_ID})
        db.commit()
    print(f"  Inspections: {insp_count}")

    # Safety Violations (every log → ~21 per project)
    sv_count = 0
    viol_type_ids = [r[0] for r in db.execute(text(
        "SELECT id FROM agcm_violation_types WHERE company_id = :cid"
    ), {"cid": COMPANY_ID}).fetchall()]
    if viol_type_ids:
        for log_id, pid, log_date in log_ids:
            for _ in range(random.randint(1, 2)):
                sv_count += 1
                db.execute(text(
                    "INSERT INTO agcm_safety_violations (company_id, sequence_name, name, "
                    "violation_notice, violation_type_id, dailylog_id, project_id, created_by) "
                    "VALUES (:cid, :seq, :name, :notice, :tid, :log, :pid, :uid)"
                ), {"cid": COMPANY_ID, "seq": f"SV{sv_count:05d}",
                    "name": random.choice(SAFETY_DESCRIPTIONS),
                    "notice": random.choice(["Verbal warning", "Written notice", "Work stopped"]),
                    "tid": random.choice(viol_type_ids),
                    "log": log_id, "pid": pid, "uid": USER_ID})
        db.commit()
    print(f"  Safety Violations: {sv_count}")

    # Delays (every log, 1-2 per log → ~25-40 per project)
    delay_count = 0
    for log_id, pid, log_date in log_ids:
        for _ in range(random.randint(1, 2)):
            delay_count += 1
            db.execute(text(
                "INSERT INTO agcm_delays (company_id, sequence_name, name, reason, "
                "delay, reported_by, partner_id, dailylog_id, project_id, created_by) "
                "VALUES (:cid, :seq, :name, :reason, :delay, :reported, :partner, :log, :pid, :uid)"
            ), {"cid": COMPANY_ID, "seq": f"D{delay_count:05d}",
                "name": f"Delay #{delay_count}",
                "reason": random.choice(DELAY_REASONS),
                "delay": f"{random.randint(1, 8)} hours",
                "reported": random.choice(VISITOR_NAMES),
                "partner": USER_ID,
                "log": log_id, "pid": pid, "uid": USER_ID})
    db.commit()
    print(f"  Delays: {delay_count}")

    # Deficiencies (every log → ~21 per project)
    def_count = 0
    for log_id, pid, log_date in log_ids:
            def_count += 1
            db.execute(text(
                "INSERT INTO agcm_deficiencies (company_id, sequence_name, name, "
                "description, dailylog_id, project_id, created_by) "
                "VALUES (:cid, :seq, :name, :desc, :log, :pid, :uid)"
            ), {"cid": COMPANY_ID, "seq": f"DEF{def_count:05d}",
                "name": random.choice(DEFICIENCY_NAMES),
                "desc": f"Found at {random.choice(LOCATIONS)}. Requires attention.",
                "log": log_id, "pid": pid, "uid": USER_ID})
    db.commit()
    print(f"  Deficiencies: {def_count}")

    # Accidents (every log → ~21 per project)
    acc_count = 0
    acc_type_ids = [r[0] for r in db.execute(text(
        "SELECT id FROM agcm_accident_types WHERE company_id = :cid"
    ), {"cid": COMPANY_ID}).fetchall()]
    if acc_type_ids:
        for log_id, pid, log_date in log_ids:
                acc_count += 1
                db.execute(text(
                    "INSERT INTO agcm_accidents (company_id, sequence_name, name, "
                    "accident_type_id, resolution, location, dailylog_id, project_id, created_by) "
                    "VALUES (:cid, :seq, :name, :tid, :res, :loc, :log, :pid, :uid)"
                ), {"cid": COMPANY_ID, "seq": f"ACC{acc_count:05d}",
                    "name": f"Incident #{acc_count}",
                    "tid": random.choice(acc_type_ids),
                    "res": random.choice(["First aid", "Sent to clinic", "Near miss documented"]),
                    "loc": random.choice(LOCATIONS),
                    "log": log_id, "pid": pid, "uid": USER_ID})
        db.commit()
    print(f"  Accidents: {acc_count}")


def seed_approval_chains(db):
    """Seed approval chains (requires base_automation module with correct enum)."""
    print("\n--- Seeding approval chains ---")
    try:
        from agcm_addons.agcm.scripts.seed_approval_chains import seed as _seed_chains
        _seed_chains(db, COMPANY_ID, USER_ID)
    except Exception as e:
        print(f"  Skipped (base_automation enum mismatch): {e}")


def main():
    db = Session()
    try:
        clear_all_agcm_data(db)

        print("\n" + "=" * 60)
        print("SEEDING DEMO DATA")
        print("=" * 60)

        project_ids = seed_projects(db)
        seed_lookups(db)
        seed_cost_codes(db, project_ids)
        seed_budgets(db, project_ids)
        seed_rfis(db, project_ids)
        seed_change_orders(db, project_ids)
        seed_submittals(db, project_ids)
        seed_purchase_orders(db, project_ids)
        seed_invoices_and_bills(db, project_ids)
        seed_vendors(db)
        seed_project_members(db, project_ids)
        seed_module_settings(db)

        # Seed original AGCM daily log data (daily logs, weather, manpower,
        # notes, inspections, visitors, safety violations, delays, deficiencies, accidents)
        seed_daily_log_data(db, project_ids)

        # Approval chains use a separate session to avoid rollback on error
        try:
            seed_approval_chains(Session())
        except Exception:
            pass

        # Final counts
        print("\n" + "=" * 60)
        print("SEED COMPLETE — Summary")
        print("=" * 60)
        for table, label in [
            ("agcm_projects", "Projects"),
            ("agcm_daily_activity_logs", "Daily Logs"),
            ("agcm_manpower", "Manpower"),
            ("agcm_weather", "Weather"),
            ("agcm_notes", "Notes"),
            ("agcm_inspections", "Inspections"),
            ("agcm_visitors", "Visitors"),
            ("agcm_safety_violations", "Safety Violations"),
            ("agcm_delays", "Delays"),
            ("agcm_deficiencies", "Deficiencies"),
            ("agcm_accidents", "Accidents"),
            ("agcm_rfis", "RFIs"),
            ("agcm_change_orders", "Change Orders"),
            ("agcm_submittals", "Submittals"),
            ("agcm_purchase_orders", "Purchase Orders"),
            ("agcm_budgets", "Budget Lines"),
            ("agcm_invoices", "Invoices"),
            ("agcm_bills", "Bills"),
            ("agcm_tax_rates", "Tax Rates"),
            ("agcm_vendors", "Vendors"),
            ("agcm_project_members", "Project Members"),
            ("agcm_settings", "Module Settings"),
            ("agcm_cost_codes", "Cost Codes"),
        ]:
            try:
                count = db.execute(text(f"SELECT count(*) FROM {table}")).scalar()
                print(f"  {label}: {count}")
            except Exception:
                print(f"  {label}: [table not found]")

    finally:
        db.close()


if __name__ == "__main__":
    main()
