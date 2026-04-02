"""Seed demo data for phases 3-6: agcm_resource, agcm_safety, agcm_portal, agcm_reporting."""

import json
import os
import sys
import random
import importlib.util
from datetime import date, datetime, timedelta, timezone

random.seed(88)

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

    # Load base agcm models
    for mf in ["lookups", "project", "daily_activity_log", "manpower", "weather", "notes",
                "inspection", "accident", "visitor", "safety_violation", "delay", "deficiency", "photo"]:
        load_model(f"_b_{mf}", os.path.join(addon, "agcm", "models", f"{mf}.py"))
    for mf in ["cost_catalog", "assembly", "estimate", "estimate_markup", "proposal", "takeoff"]:
        load_model(f"_e_{mf}", os.path.join(addon, "agcm_estimate", "models", f"{mf}.py"))
    for mf in ["purchase_order", "subcontract", "vendor_bill"]:
        load_model(f"_p_{mf}", os.path.join(addon, "agcm_procurement", "models", f"{mf}.py"))

    try:
        from app.models import User, Company
    except Exception:
        pass

    # Load Phase 3-6 models
    mod_worker = load_model("_r_worker", os.path.join(addon, "agcm_resource", "models", "worker.py"))
    mod_equipment = load_model("_r_equipment", os.path.join(addon, "agcm_resource", "models", "equipment.py"))
    mod_timesheet = load_model("_r_timesheet", os.path.join(addon, "agcm_resource", "models", "timesheet.py"))
    mod_equip_assign = load_model("_r_equip_assign", os.path.join(addon, "agcm_resource", "models", "equipment_assignment.py"))

    mod_checklist = load_model("_s_checklist", os.path.join(addon, "agcm_safety", "models", "checklist.py"))
    mod_inspection = load_model("_s_inspection", os.path.join(addon, "agcm_safety", "models", "inspection.py"))
    mod_punch = load_model("_s_punch", os.path.join(addon, "agcm_safety", "models", "punch_list.py"))
    mod_incident = load_model("_s_incident", os.path.join(addon, "agcm_safety", "models", "incident.py"))

    mod_selection = load_model("_portal_selection", os.path.join(addon, "agcm_portal", "models", "selection.py"))
    mod_bid = load_model("_portal_bid", os.path.join(addon, "agcm_portal", "models", "bid.py"))
    mod_portal_cfg = load_model("_portal_config", os.path.join(addon, "agcm_portal", "models", "portal_config.py"))

    mod_report_def = load_model("_rpt_def", os.path.join(addon, "agcm_reporting", "models", "report_definition.py"))
    mod_dash_widget = load_model("_rpt_dash", os.path.join(addon, "agcm_reporting", "models", "dashboard_widget.py"))

    Worker = mod_worker.Worker
    Equipment = mod_equipment.Equipment
    Timesheet = mod_timesheet.Timesheet
    EquipmentAssignment = mod_equip_assign.EquipmentAssignment

    ChecklistTemplate = mod_checklist.ChecklistTemplate
    ChecklistTemplateItem = mod_checklist.ChecklistTemplateItem
    SafetyInspection = mod_inspection.SafetyInspection
    SafetyInspectionItem = mod_inspection.SafetyInspectionItem
    PunchListItem = mod_punch.PunchListItem
    IncidentReport = mod_incident.IncidentReport

    Selection = mod_selection.Selection
    SelectionOption = mod_selection.SelectionOption
    BidPackage = mod_bid.BidPackage
    BidSubmission = mod_bid.BidSubmission
    PortalConfig = mod_portal_cfg.PortalConfig

    ReportDefinition = mod_report_def.AGCMReportDefinition
    ReportSchedule = mod_report_def.AGCMReportSchedule
    DashboardLayout = mod_dash_widget.AGCMDashboardLayout
    DashboardWidget = mod_dash_widget.AGCMDashboardWidget

    from app.db.base import Base
    from sqlalchemy import text as _text, inspect as _inspect

    # Ensure all required tables exist
    inspector = _inspect(engine)
    existing_tables = set(inspector.get_table_names())
    target_tables = [
        "agcm_workers", "agcm_equipment", "agcm_timesheets", "agcm_equipment_assignments",
        "agcm_checklist_templates", "agcm_checklist_template_items",
        "agcm_safety_inspections", "agcm_safety_inspection_items",
        "agcm_punch_list_items", "agcm_incident_reports",
        "agcm_selections", "agcm_selection_options",
        "agcm_bid_packages", "agcm_bid_submissions",
        "agcm_portal_configs",
        "agcm_report_definitions", "agcm_report_schedules",
        "agcm_dashboard_layouts", "agcm_dashboard_widgets",
    ]
    missing = [t for t in target_tables if t not in existing_tables]
    if missing:
        # Drop conflicting indexes from the old inspections_v2 table that clash with new model index names
        with engine.begin() as conn:
            for idx_name in [
                "ix_agcm_insp_v2_project", "ix_agcm_insp_v2_status", "ix_agcm_insp_v2_company",
                "ix_agcm_insp_item_inspection",
            ]:
                try:
                    conn.execute(_text(f"DROP INDEX IF EXISTS {idx_name}"))
                except Exception:
                    pass

        tables_to_create = [Base.metadata.tables[t] for t in missing if t in Base.metadata.tables]
        if tables_to_create:
            with engine.begin() as conn:
                for tbl in tables_to_create:
                    try:
                        tbl.create(conn, checkfirst=True)
                    except Exception as e:
                        print(f"  Warning: could not create {tbl.name}: {e}")

    # Re-create session after DDL
    db = Session()

    # ===================================================================
    # Reference data
    # ===================================================================
    TRADES = [
        "Electrician", "Plumber", "Carpenter", "Iron Worker", "Mason",
        "HVAC Technician", "Painter", "Roofer", "Glazier", "Welder",
        "Concrete Finisher", "Drywall Installer", "Tile Setter", "Insulator",
        "Sheet Metal Worker", "Pipefitter", "Laborer", "Equipment Operator",
    ]

    FIRST_NAMES = [
        "James", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas",
        "Charles", "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Paul",
        "Andrew", "Joshua", "Kenneth", "Kevin", "Maria", "Patricia", "Linda", "Barbara",
        "Elizabeth", "Jennifer", "Susan", "Jessica", "Sarah", "Karen", "Lisa", "Nancy",
        "Betty", "Sandra", "Margaret", "Ashley", "Dorothy", "Kimberly", "Emily", "Donna",
        "Carlos", "Miguel", "Jose", "Juan", "Pedro", "Luis", "Jorge", "Alejandro",
        "Fernando", "Ricardo", "Diego", "Marco", "Rafael", "Roberto", "Francisco", "Eduardo",
        "Hector", "Oscar", "Victor", "Sergio", "Angel", "Ramon", "Andres", "Manuel",
    ]
    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
        "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
        "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
        "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen",
        "Hill", "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera",
    ]

    CERTIFICATIONS_POOL = [
        "OSHA 10-Hour", "OSHA 30-Hour", "First Aid/CPR", "Confined Space Entry",
        "Fall Protection Certified", "Scaffold Competent Person", "Forklift Certified",
        "Crane Operator NCCCO", "AWS Certified Welder", "EPA 608 Universal",
        "Master Electrician License", "Journeyman Plumber License", "CDL Class A",
    ]

    EQUIPMENT_DATA = [
        ("CAT 320 Excavator", "Excavator", "Caterpillar", "320F", 2800, 380),
        ("CAT 950 Wheel Loader", "Wheel Loader", "Caterpillar", "950M", 2200, 300),
        ("Liebherr LTM 1100 Crane", "Crane", "Liebherr", "LTM 1100-4.2", 5500, 750),
        ("Komatsu PC210 Excavator", "Excavator", "Komatsu", "PC210LC-11", 2600, 350),
        ("JLG 600S Boom Lift", "Boom Lift", "JLG", "600S", 950, 130),
        ("Genie S-65 Boom Lift", "Boom Lift", "Genie", "S-65", 900, 125),
        ("CAT D6 Dozer", "Dozer", "Caterpillar", "D6T", 3200, 430),
        ("Volvo A30G Articulated Truck", "Articulated Truck", "Volvo", "A30G", 2400, 325),
        ("Bomag BW213 Compactor", "Compactor", "Bomag", "BW213D-5", 1100, 150),
        ("Toyota 8FGU25 Forklift", "Forklift", "Toyota", "8FGU25", 450, 65),
        ("Hyster H80FT Forklift", "Forklift", "Hyster", "H80FT", 480, 70),
        ("Wacker Neuson DPU6555 Plate Compactor", "Plate Compactor", "Wacker Neuson", "DPU6555", 180, 25),
        ("Multiquip Concrete Mixer", "Concrete Mixer", "Multiquip", "MC94SH", 350, 50),
        ("Putzmeister BSF 36Z Concrete Pump", "Concrete Pump", "Putzmeister", "BSF 36Z.16H", 4200, 570),
        ("CAT 930M Wheel Loader", "Wheel Loader", "Caterpillar", "930M", 1800, 245),
        ("Bobcat T770 Track Loader", "Track Loader", "Bobcat", "T770", 950, 130),
        ("Ingersoll Rand P185 Compressor", "Air Compressor", "Ingersoll Rand", "P185WJD", 350, 50),
        ("Atlas Copco XAS 185 Compressor", "Air Compressor", "Atlas Copco", "XAS 185", 380, 55),
        ("Wacker Neuson SW16 Skid Steer", "Skid Steer", "Wacker Neuson", "SW16", 650, 90),
        ("Link-Belt TCC-750 Telescopic Crane", "Crane", "Link-Belt", "TCC-750", 4800, 650),
        ("John Deere 310L Backhoe", "Backhoe", "John Deere", "310L", 1400, 190),
        ("Kubota KX040 Mini Excavator", "Mini Excavator", "Kubota", "KX040-4", 850, 115),
        ("Hilti TE 3000-AVR Breaker", "Breaker", "Hilti", "TE 3000-AVR", 250, 35),
        ("Husqvarna K 770 Concrete Saw", "Concrete Saw", "Husqvarna", "K 770", 120, 18),
        ("Genie GS-1930 Scissor Lift", "Scissor Lift", "Genie", "GS-1930", 350, 50),
        ("JLG 3246ES Scissor Lift", "Scissor Lift", "JLG", "3246ES", 380, 55),
        ("Vermeer D24x40 Drill", "Directional Drill", "Vermeer", "D24x40 S3", 2200, 300),
        ("CAT 308 Mini Excavator", "Mini Excavator", "Caterpillar", "308 CR", 1100, 150),
        ("Volvo EC220E Excavator", "Excavator", "Volvo", "EC220E", 2500, 340),
        ("Terex RT 555-1 Crane", "Crane", "Terex", "RT 555-1", 3800, 520),
        ("Wacker Neuson 6003 Dumper", "Dumper", "Wacker Neuson", "6003", 550, 75),
        ("Takeuchi TL12V2 Track Loader", "Track Loader", "Takeuchi", "TL12V2", 900, 125),
        ("DeWalt DW745 Table Saw", "Table Saw", "DeWalt", "DW745", 85, 12),
        ("Lincoln Electric Ranger 250 GXT Welder", "Welder/Generator", "Lincoln Electric", "Ranger 250 GXT", 300, 42),
        ("Miller Trailblazer 325 Welder", "Welder/Generator", "Miller", "Trailblazer 325", 320, 45),
        ("Generac XC6500 Generator", "Generator", "Generac", "XC6500E", 250, 35),
        ("Honda EU7000iS Generator", "Generator", "Honda", "EU7000iS", 280, 40),
        ("Manitou MT 1840 Telehandler", "Telehandler", "Manitou", "MT 1840", 1600, 220),
        ("JCB 540-170 Telehandler", "Telehandler", "JCB", "540-170", 1700, 235),
        ("Multiquip QP4TH Trash Pump", "Pump", "Multiquip", "QP4TH", 200, 28),
        ("Wacker Neuson PT3 Pump", "Pump", "Wacker Neuson", "PT3", 180, 25),
        ("CAT 140 Motor Grader", "Motor Grader", "Caterpillar", "140", 3400, 460),
    ]

    LOCATIONS = [
        "Building A - Ground Floor", "Building A - 2nd Floor", "Building A - 3rd Floor",
        "Building A - Roof", "Building B - Ground Floor", "Building B - 2nd Floor",
        "Building C - Basement", "Building C - Ground Floor", "Parking Garage Level 1",
        "Parking Garage Level 2", "Site Entrance", "Loading Dock", "Mechanical Room",
        "Electrical Room", "Elevator Shaft", "Stairwell A", "Stairwell B",
        "Lobby", "Conference Wing", "Cafeteria", "Restrooms 1st Floor", "Utility Corridor",
        "North Exterior Wall", "South Exterior Wall", "East Wing", "West Wing",
    ]

    TASK_DESCRIPTIONS = [
        "Rough electrical wiring installation", "Plumbing rough-in for 2nd floor",
        "Framing interior walls", "Installing ductwork", "Concrete pour preparation",
        "Steel beam installation", "Drywall hanging", "Tile installation bathroom",
        "Paint prep and priming", "Roofing membrane application",
        "Window installation", "Fire sprinkler piping", "Insulation installation",
        "Conduit routing and pull", "Pipe fitting and soldering",
        "Block wall construction", "Ceiling grid installation", "Floor leveling compound",
        "Cabinet installation", "Finish carpentry trim work",
        "Fire alarm wiring", "Elevator shaft framing", "Waterproofing application",
        "Grading and compaction", "Slab on grade forming",
    ]

    # ===================================================================
    # PHASE 3: agcm_resource
    # ===================================================================
    print("\n=== Seeding Resource Data ===")

    # --- Workers ---
    worker_count = 0
    worker_ids = []
    worker_rates = {}  # worker_id -> (hourly_rate, overtime_rate)
    skill_levels = ["apprentice", "journeyman", "journeyman", "master", "foreman", "superintendent"]
    worker_statuses = ["active", "active", "active", "active", "active", "inactive", "on_leave"]

    for pid in PROJECT_IDS:
        for i in range(5):
            worker_count += 1
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            skill = random.choice(skill_levels)
            trade = random.choice(TRADES)
            base_rate = {
                "apprentice": random.uniform(22, 32),
                "journeyman": random.uniform(35, 55),
                "master": random.uniform(55, 75),
                "foreman": random.uniform(60, 85),
                "superintendent": random.uniform(75, 110),
            }[skill]
            hr = round(base_rate, 2)
            otr = round(hr * 1.5, 2)
            num_certs = random.randint(1, 4)
            certs = json.dumps(random.sample(CERTIFICATIONS_POOL, min(num_certs, len(CERTIFICATIONS_POOL))))

            w = Worker(
                company_id=COMPANY_ID,
                sequence_name=f"WK{worker_count:05d}",
                first_name=fn,
                last_name=ln,
                full_name=f"{fn} {ln}",
                email=f"{fn.lower()}.{ln.lower()}{worker_count}@construction.example.com",
                phone=f"(512) {random.randint(200,999)}-{random.randint(1000,9999)}",
                status=random.choice(worker_statuses),
                skill_level=skill,
                trade=trade,
                hourly_rate=hr,
                overtime_rate=otr,
                certifications=certs,
                hire_date=date(2020, 1, 1) + timedelta(days=random.randint(0, 1800)),
                is_subcontractor=random.random() < 0.25,
            )
            db.add(w)
            db.flush()
            worker_ids.append(w.id)
            worker_rates[w.id] = (hr, otr)

    db.commit()
    print(f"  Workers: {worker_count}")

    # --- Equipment ---
    equip_count = 0
    equip_ids = []
    equip_rates = {}  # equip_id -> daily_rate
    ownership_types = ["owned", "owned", "rented", "rented", "leased"]
    equip_statuses = ["available", "in_use", "in_use", "in_use", "maintenance", "retired"]

    for name, etype, make, model_name, daily, hourly in EQUIPMENT_DATA:
        equip_count += 1
        year = random.randint(2016, 2024)
        serial = f"{make[:3].upper()}-{random.randint(100000, 999999)}"
        status = random.choice(equip_statuses)
        cur_proj = random.choice(PROJECT_IDS) if status == "in_use" else None
        lmd = date(2025, 1, 1) + timedelta(days=random.randint(-180, 0))
        nmd = lmd + timedelta(days=random.randint(30, 180))

        eq = Equipment(
            company_id=COMPANY_ID,
            sequence_name=f"EQ{equip_count:05d}",
            name=name,
            equipment_type=etype,
            make=make,
            model=model_name,
            year=year,
            serial_number=serial,
            status=status,
            ownership_type=random.choice(ownership_types),
            daily_rate=float(daily),
            hourly_rate=float(hourly),
            current_project_id=cur_proj,
            current_location=random.choice(LOCATIONS) if status == "in_use" else None,
            last_maintenance_date=lmd,
            next_maintenance_date=nmd,
        )
        db.add(eq)
        db.flush()
        equip_ids.append(eq.id)
        equip_rates[eq.id] = float(daily)

    db.commit()
    print(f"  Equipment: {equip_count}")

    # --- Timesheets ---
    ts_count = 0
    ts_statuses = ["draft", "submitted", "submitted", "approved", "approved", "approved", "rejected"]
    base_date = date(2025, 3, 1)

    for pid in PROJECT_IDS:
        # Each project gets timesheets from ~5 workers across ~10 days
        proj_workers = random.sample(worker_ids, min(5, len(worker_ids)))
        for wid in proj_workers:
            hr_rate, ot_rate = worker_rates[wid]
            num_days = random.randint(8, 14)
            for d in range(num_days):
                ts_date = base_date + timedelta(days=d + random.randint(0, 20))
                # Skip weekends sometimes
                if ts_date.weekday() >= 5 and random.random() < 0.6:
                    continue
                ts_count += 1
                reg_h = round(random.uniform(6, 8), 1)
                ot_h = round(random.uniform(0, 3), 1) if random.random() < 0.4 else 0
                dt_h = round(random.uniform(0, 2), 1) if random.random() < 0.1 else 0
                total_h = round(reg_h + ot_h + dt_h, 1)
                reg_cost = round(reg_h * hr_rate, 2)
                ot_cost = round(ot_h * ot_rate * 1.5, 2)
                total_cost = round(reg_cost + ot_cost + dt_h * ot_rate * 2, 2)
                status = random.choice(ts_statuses)

                clock_in_hr = random.choice([6, 7])
                clock_in = datetime(ts_date.year, ts_date.month, ts_date.day, clock_in_hr, 0)
                clock_out = clock_in + timedelta(hours=total_h)

                ts = Timesheet(
                    company_id=COMPANY_ID,
                    sequence_name=f"TS{ts_count:05d}",
                    worker_id=wid,
                    project_id=pid,
                    date=ts_date,
                    regular_hours=reg_h,
                    overtime_hours=ot_h,
                    double_time_hours=dt_h,
                    total_hours=total_h,
                    regular_cost=reg_cost,
                    overtime_cost=ot_cost,
                    total_cost=total_cost,
                    clock_in=clock_in,
                    clock_out=clock_out,
                    status=status,
                    approved_by=USER_ID if status == "approved" else None,
                    approved_date=ts_date + timedelta(days=1) if status == "approved" else None,
                    task_description=random.choice(TASK_DESCRIPTIONS),
                    location=random.choice(LOCATIONS),
                )
                db.add(ts)

        if pid % 3 == 0:
            db.commit()

    db.commit()
    print(f"  Timesheets: {ts_count}")

    # --- Equipment Assignments ---
    ea_count = 0
    for pid in PROJECT_IDS:
        num_assign = random.randint(4, 7)
        proj_equip = random.sample(equip_ids, min(num_assign, len(equip_ids)))
        for eid in proj_equip:
            ea_count += 1
            assigned = date(2025, 2, 1) + timedelta(days=random.randint(0, 90))
            days = random.randint(5, 45)
            ret = assigned + timedelta(days=days) if random.random() < 0.7 else None
            dr = equip_rates[eid]
            tc = round(dr * days, 2)

            ea = EquipmentAssignment(
                company_id=COMPANY_ID,
                equipment_id=eid,
                project_id=pid,
                assigned_date=assigned,
                return_date=ret,
                daily_rate=dr,
                total_days=days,
                total_cost=tc,
            )
            db.add(ea)

    db.commit()
    print(f"  Equipment Assignments: {ea_count}")

    # ===================================================================
    # PHASE 4: agcm_safety
    # ===================================================================
    print("\n=== Seeding Safety Data ===")

    # --- Checklist Templates & Items ---
    TEMPLATES = [
        ("Foundation Inspection", "structural", [
            "Verify footing dimensions match approved drawings",
            "Check rebar placement, size, and spacing",
            "Inspect formwork alignment and bracing",
            "Confirm anchor bolt placement and projection",
            "Verify soil bearing capacity test results",
            "Check waterproofing membrane installation",
            "Inspect vapor barrier continuity",
        ]),
        ("Framing Inspection", "structural", [
            "Verify stud spacing and size per plans",
            "Check header sizes over openings",
            "Inspect hold-down and strap connections",
            "Verify sheathing nailing pattern",
            "Check fire blocking installation",
            "Inspect top plate lap splices",
        ]),
        ("Electrical Rough-In", "MEP", [
            "Verify wire gauge matches circuit amperage",
            "Check box fill calculations compliance",
            "Inspect grounding and bonding continuity",
            "Verify AFCI/GFCI protection per code",
            "Check conduit support and spacing",
            "Inspect panel schedule matches installed circuits",
            "Verify emergency circuit separation",
        ]),
        ("Plumbing Rough-In", "MEP", [
            "Verify pipe sizing per fixture unit calculation",
            "Check DWV slope (1/4\" per foot minimum)",
            "Inspect pressure test results (min 50 PSI 15 min)",
            "Verify cleanout locations per code",
            "Check water heater installation clearances",
            "Inspect backflow prevention devices",
        ]),
        ("HVAC Installation", "MEP", [
            "Verify duct sizing per load calculation",
            "Check duct sealing at all joints (mastic/tape)",
            "Inspect refrigerant line brazing quality",
            "Verify thermostat placement (5ft, interior wall)",
            "Check condensate drain routing and trap",
            "Inspect equipment clearances for service access",
        ]),
        ("Roofing Inspection", "envelope", [
            "Verify underlayment installation and overlap",
            "Check flashing at all penetrations",
            "Inspect valley and ridge details",
            "Verify drip edge installation",
            "Check gutter and downspout sizing",
            "Inspect attic ventilation (1:150 ratio)",
        ]),
        ("Fire Protection", "life_safety", [
            "Verify sprinkler head spacing per NFPA 13",
            "Check fire alarm device placement per NFPA 72",
            "Inspect fire-rated assembly penetrations",
            "Verify fire door ratings and hardware",
            "Check fire extinguisher placement (75ft travel)",
            "Inspect fire pump test results",
            "Verify standpipe connection accessibility",
        ]),
        ("Concrete Placement", "structural", [
            "Verify mix design matches specifications",
            "Check slump test results (4\" +/- 1\")",
            "Inspect rebar coverage and chair placement",
            "Verify control joint layout",
            "Check curing compound application",
            "Inspect cylinder test schedule compliance",
        ]),
        ("Waterproofing Inspection", "envelope", [
            "Verify surface preparation and priming",
            "Check membrane thickness (wet mil gauge)",
            "Inspect lap seams and termination details",
            "Verify drainage board installation",
            "Check protection board over membrane",
            "Inspect flood test results (24-hour minimum)",
        ]),
        ("Final / Punch Walk", "closeout", [
            "Verify all finish surfaces free of damage",
            "Check all hardware operation (doors, locks, closers)",
            "Inspect paint touch-ups and wall finish quality",
            "Verify all MEP systems operational",
            "Check flooring transitions and thresholds",
            "Inspect all signage and room numbering",
            "Verify ADA compliance (grab bars, clearances)",
            "Check life safety systems tested and tagged",
        ]),
    ]

    tpl_count = 0
    tpl_item_count = 0
    template_ids = []

    for tpl_name, category, items in TEMPLATES:
        tpl_count += 1
        tpl = ChecklistTemplate(
            company_id=COMPANY_ID,
            name=tpl_name,
            category=category,
            is_active=True,
        )
        db.add(tpl)
        db.flush()
        template_ids.append(tpl.id)

        for j, desc in enumerate(items):
            tpl_item_count += 1
            item = ChecklistTemplateItem(
                template_id=tpl.id,
                company_id=COMPANY_ID,
                description=desc,
                required=random.random() < 0.85,
                display_order=j,
            )
            db.add(item)

    db.commit()
    print(f"  Checklist Templates: {tpl_count}, Template Items: {tpl_item_count}")

    # --- Safety Inspections & Items ---
    insp_count = 0
    insp_item_count = 0
    insp_statuses = ["scheduled", "in_progress", "passed", "passed", "passed", "failed", "conditional"]
    inspectors = [
        ("John Mitchell", "City Building Dept"), ("Sarah Chen", "AHJ Fire Marshal"),
        ("Robert Alvarez", "MEP Engineering Inc"), ("Linda Park", "Structural Solutions"),
        ("David Kowalski", "Third Party Testing"), ("Maria Santos", "OSHA Compliance Group"),
        ("James O'Brien", "Quality Assurance LLC"), ("Angela Wu", "Safety First Consultants"),
    ]
    insp_types = ["foundation", "framing", "rough_electrical", "rough_plumbing", "rough_HVAC",
                  "insulation", "drywall", "fire_protection", "final", "roofing", "concrete"]

    for pid in PROJECT_IDS:
        num_insp = random.randint(5, 7)
        for i in range(num_insp):
            insp_count += 1
            inspector_name, inspector_co = random.choice(inspectors)
            tpl_id = random.choice(template_ids)
            status = random.choice(insp_statuses)
            sched = date(2025, 2, 1) + timedelta(days=random.randint(0, 150))
            completed = sched + timedelta(days=random.randint(0, 5)) if status in ("passed", "failed", "conditional") else None
            result_map = {
                "passed": "pass", "failed": "fail", "conditional": "conditional",
                "scheduled": None, "in_progress": None,
            }

            insp = SafetyInspection(
                company_id=COMPANY_ID,
                sequence_name=f"SI{insp_count:05d}",
                project_id=pid,
                template_id=tpl_id,
                inspector_name=inspector_name,
                inspector_company=inspector_co,
                inspection_type=random.choice(insp_types),
                status=status,
                scheduled_date=sched,
                completed_date=completed,
                location=random.choice(LOCATIONS),
                overall_result=result_map.get(status),
            )
            db.add(insp)
            db.flush()

            # Items per inspection
            num_items = random.randint(5, 8)
            item_results = ["pass", "pass", "pass", "pass", "fail", "na"]
            for j in range(num_items):
                insp_item_count += 1
                res = random.choice(item_results) if status not in ("scheduled",) else None
                item = SafetyInspectionItem(
                    inspection_id=insp.id,
                    company_id=COMPANY_ID,
                    description=f"Inspection item #{j+1} - check compliance",
                    result=res,
                    notes=f"Noted: {random.choice(['OK', 'Minor issue', 'Needs follow-up', 'Acceptable'])}" if res else None,
                    display_order=j,
                )
                db.add(item)

        if pid % 4 == 0:
            db.commit()

    db.commit()
    print(f"  Safety Inspections: {insp_count}, Inspection Items: {insp_item_count}")

    # --- Punch List Items ---
    punch_count = 0
    punch_statuses = ["open", "open", "in_progress", "in_progress", "completed", "verified"]
    punch_priorities = ["low", "medium", "medium", "medium", "high", "critical"]

    PUNCH_TITLES = [
        "Paint touch-up lobby ceiling", "Drywall crack repair 2nd floor corridor",
        "Cabinet door alignment kitchen unit 3", "Tile grout missing bathroom 204",
        "Electrical cover plate missing room 301", "HVAC diffuser not balanced suite 102",
        "Door closer adjustment main entrance", "Baseboard gap at corner office 405",
        "Window sealant bead incomplete north wall", "Carpet seam visible hallway B",
        "Light fixture flickering conference room A", "Ceiling grid sagging above reception",
        "Fire caulk missing at pipe penetration", "Handrail loose at stairwell B landing",
        "Floor transition strip missing elevator lobby", "Paint overspray on window frame 2F",
        "Plumbing leak under sink breakroom", "Missing escutcheon plate sprinkler head",
        "Damaged outlet cover plate room 208", "Scratched door hardware suite 301",
        "Unfinished caulk at countertop backsplash", "Misaligned switch plate conference B",
        "Stained ceiling tile mechanical room", "Cracked floor tile entry vestibule",
        "Missing access panel above ceiling grid", "Improperly graded landscape at entry",
        "Exterior light not operational south wall", "Parking lot striping incomplete",
        "ADA sign missing at restroom", "Fire extinguisher cabinet dented level 1",
        "Concrete spall at loading dock", "Expansion joint sealant missing level P2",
        "Roof drain cap missing section 4", "Condensation on HVAC duct above ceiling",
        "Acoustic panel loose in auditorium", "Elevator cab finish scratched",
    ]

    for pid in PROJECT_IDS:
        num_punch = random.randint(6, 9)
        for i in range(num_punch):
            punch_count += 1
            status = random.choice(punch_statuses)
            priority = random.choice(punch_priorities)
            due = date(2025, 4, 1) + timedelta(days=random.randint(0, 60))
            completed = due - timedelta(days=random.randint(0, 5)) if status in ("completed", "verified") else None
            verified = completed + timedelta(days=random.randint(1, 3)) if status == "verified" and completed else None

            p = PunchListItem(
                company_id=COMPANY_ID,
                sequence_name=f"PL{punch_count:05d}",
                project_id=pid,
                title=random.choice(PUNCH_TITLES),
                description=f"Deficiency noted during walk-through. Requires correction before substantial completion.",
                status=status,
                priority=priority,
                location=random.choice(LOCATIONS),
                trade=random.choice(TRADES[:10]),
                assigned_to=USER_ID if status != "open" else None,
                due_date=due,
                completed_date=completed,
                verified_date=verified,
                verified_by=USER_ID if status == "verified" else None,
            )
            db.add(p)

    db.commit()
    print(f"  Punch List Items: {punch_count}")

    # --- Incident Reports ---
    incident_count = 0
    severities = ["near_miss", "near_miss", "near_miss", "first_aid", "first_aid", "medical", "lost_time"]
    inc_statuses = ["reported", "investigating", "resolved", "resolved", "closed"]

    INCIDENT_DATA = [
        ("Worker tripped over unsecured extension cord", "Trip hazard", "Extension cord across walkway not secured", "Implement cord covers on all walkways; add to daily inspection"),
        ("Falling debris from overhead work struck hardhat", "Struck by", "Overhead demolition without barricade below", "Establish controlled access zones; install debris netting"),
        ("Ladder slipped on wet surface", "Fall from elevation", "Wet floor from rain without barricade", "Deploy anti-slip mats; barricade wet areas immediately"),
        ("Worker strained back lifting heavy pipe", "Overexertion", "Improper lifting technique; no mechanical aid", "Mandatory buddy lift over 50 lbs; provide mechanical hoist"),
        ("Nail gun discharged into worker's hand", "Struck by", "Trigger lock not engaged; hand in line of fire", "Retrain on nail gun safety; enforce trigger lock policy"),
        ("Worker exposed to concrete dust without mask", "Exposure", "RPE not worn during cutting operation", "Enforce PPE policy; provide N95 dust masks at cutting stations"),
        ("Scaffolding plank broke under load", "Fall from elevation", "Plank not rated for load; no inspection tag", "Implement scaffold tagging system; daily competent person inspection"),
        ("Excavation cave-in near worker", "Cave-in", "Trench box not installed above 5ft depth", "Mandatory trench protection over 4ft; retrain excavation competent person"),
        ("Forklift struck pedestrian at blind corner", "Struck by", "No spotter used; poor visibility at corner", "Install convex mirrors; mandatory spotter for blind corners"),
        ("Arc flash during panel energization", "Electrical", "Panel not properly de-energized; no LOTO", "Enforce LOTO procedures; require arc flash PPE for all panel work"),
        ("Worker cut by unguarded circular saw", "Laceration", "Blade guard removed and not replaced", "Daily tool inspection; zero tolerance for guard removal"),
        ("Heat exhaustion during summer concrete pour", "Heat illness", "Inadequate hydration breaks in high heat", "Mandatory 15-min breaks every hour above 90F; provide cooling stations"),
        ("Chemical splash on arm during cleaning", "Exposure", "Improper PPE for chemical handling", "Provide chemical-resistant gloves and splash goggles; update SDS access"),
        ("Boom lift contact with overhead power line", "Electrical", "No spotter; proximity to energized line", "Implement 10ft clearance rule; require spotter for all aerial work near lines"),
        ("Material fell from crane during lift", "Struck by", "Rigging failure; overloaded sling", "Re-certify riggers; implement lift plan review for loads over 75%"),
    ]

    for pid in PROJECT_IDS:
        num_incidents = random.randint(2, 4)
        chosen = random.sample(INCIDENT_DATA, min(num_incidents, len(INCIDENT_DATA)))
        for title, desc_short, root_cause, corrective in chosen:
            incident_count += 1
            severity = random.choice(severities)
            status = random.choice(inc_statuses)
            inc_date = date(2025, 2, 1) + timedelta(days=random.randint(0, 120))
            osha = severity in ("medical", "lost_time")
            days = random.randint(1, 15) if severity == "lost_time" else 0

            inc = IncidentReport(
                company_id=COMPANY_ID,
                sequence_name=f"IR{incident_count:05d}",
                project_id=pid,
                title=title,
                description=f"{desc_short}: {title}. Occurred during normal work operations.",
                severity=severity,
                status=status,
                incident_date=inc_date,
                incident_time=f"{random.randint(6,16):02d}:{random.choice(['00','15','30','45'])}",
                location=random.choice(LOCATIONS),
                injured_party=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}" if severity != "near_miss" else None,
                root_cause=root_cause,
                corrective_action=corrective,
                reported_by=USER_ID,
                investigated_by=USER_ID if status in ("resolved", "closed") else None,
                investigation_date=inc_date + timedelta(days=random.randint(1, 5)) if status in ("resolved", "closed") else None,
                closed_date=inc_date + timedelta(days=random.randint(5, 20)) if status == "closed" else None,
                osha_recordable=osha,
                days_lost=days,
            )
            db.add(inc)

    db.commit()
    print(f"  Incident Reports: {incident_count}")

    # ===================================================================
    # PHASE 5: agcm_portal
    # ===================================================================
    print("\n=== Seeding Portal Data ===")

    # --- Selections & Options ---
    sel_count = 0
    opt_count = 0
    sel_statuses = ["pending", "presented", "presented", "approved", "approved", "rejected"]

    SELECTION_CATEGORIES = [
        ("Flooring", [
            ("Engineered Hardwood - Oak", 8.50, "sf"),
            ("Luxury Vinyl Plank - Premium", 5.75, "sf"),
            ("Porcelain Tile 24x24", 12.00, "sf"),
            ("Polished Concrete", 6.00, "sf"),
        ]),
        ("Countertops", [
            ("Quartz - Cambria", 85.00, "sf"),
            ("Granite - Level 3", 65.00, "sf"),
            ("Solid Surface - Corian", 55.00, "sf"),
            ("Butcher Block - Walnut", 75.00, "sf"),
        ]),
        ("Fixtures - Lighting", [
            ("Recessed LED 6\" Canless", 45.00, "ea"),
            ("Pendant - Modern Brushed Nickel", 185.00, "ea"),
            ("Track Lighting - 4ft LED", 220.00, "ea"),
            ("Chandelier - Contemporary", 650.00, "ea"),
        ]),
        ("Paint Colors", [
            ("Benjamin Moore - Simply White", 65.00, "gal"),
            ("Sherwin Williams - Agreeable Gray", 65.00, "gal"),
            ("PPG - Whiskers", 60.00, "gal"),
        ]),
        ("Cabinets", [
            ("Custom Shaker - Painted White", 450.00, "lf"),
            ("Semi-Custom - Thermofoil", 280.00, "lf"),
            ("Stock - Raised Panel Oak", 180.00, "lf"),
            ("Custom Modern - Flat Panel Walnut", 550.00, "lf"),
        ]),
        ("Plumbing Fixtures", [
            ("Kohler Memoirs Toilet", 485.00, "ea"),
            ("Delta Trinsic Faucet - Chrome", 320.00, "ea"),
            ("Grohe Essence Faucet - Brushed Nickel", 410.00, "ea"),
            ("Moen Align Kitchen Faucet", 280.00, "ea"),
        ]),
        ("Hardware", [
            ("Emtek Knurled Knob - Satin Brass", 28.00, "ea"),
            ("Top Knobs Nouveau Ring Pull", 18.00, "ea"),
            ("Baldwin Hollywood Hills Lever", 95.00, "ea"),
        ]),
    ]

    for pid in PROJECT_IDS:
        num_sel = random.randint(5, 7)
        chosen_cats = random.sample(SELECTION_CATEGORIES, min(num_sel, len(SELECTION_CATEGORIES)))
        for cat_name, options in chosen_cats:
            sel_count += 1
            status = random.choice(sel_statuses)
            budget = round(random.uniform(2000, 25000), 2)
            selected_amt = round(budget * random.uniform(0.7, 1.4), 2) if status in ("approved",) else 0
            impact = round(selected_amt - budget, 2) if selected_amt else 0

            sel = Selection(
                company_id=COMPANY_ID,
                project_id=pid,
                name=f"{cat_name} Selection",
                category=cat_name.lower().replace(" - ", "_").replace(" ", "_"),
                description=f"Client selection for {cat_name.lower()} materials and finishes.",
                location=random.choice(LOCATIONS[:8]),
                status=status,
                due_date=date(2025, 3, 1) + timedelta(days=random.randint(0, 60)),
                decided_date=date(2025, 4, 1) + timedelta(days=random.randint(0, 30)) if status in ("approved", "rejected") else None,
                budget_amount=budget,
                selected_amount=selected_amt,
                budget_impact=impact,
                decided_by=f"Client #{pid}" if status in ("approved", "rejected") else None,
            )
            db.add(sel)
            db.flush()

            # Options
            recommended_idx = random.randint(0, len(options) - 1)
            selected_idx = random.randint(0, len(options) - 1) if status == "approved" else -1
            for j, (opt_name, price, unit) in enumerate(options):
                opt_count += 1
                opt = SelectionOption(
                    selection_id=sel.id,
                    company_id=COMPANY_ID,
                    name=opt_name,
                    description=f"Specification: {opt_name}. See attached sample/spec sheet.",
                    price=price,
                    unit=unit,
                    is_recommended=(j == recommended_idx),
                    is_selected=(j == selected_idx),
                    display_order=j,
                )
                db.add(opt)

    db.commit()
    print(f"  Selections: {sel_count}, Selection Options: {opt_count}")

    # --- Bid Packages & Submissions ---
    bp_count = 0
    bs_count = 0
    bp_statuses = ["open", "open", "closed", "closed", "awarded"]
    bid_trades = [
        "Electrical", "Plumbing", "HVAC", "Structural Steel", "Concrete",
        "Roofing", "Fire Protection", "Painting", "Masonry", "Glazing",
        "Drywall/Framing", "Flooring", "Elevator", "Site Work", "Landscaping",
    ]
    bid_sub_statuses = ["invited", "draft", "submitted", "submitted", "under_review", "awarded", "rejected", "withdrawn"]

    VENDORS_BID = [
        ("ABC Building Supply", "abc@building.example.com"),
        ("Texas Steel Co", "bids@texassteel.example.com"),
        ("Gulf Coast Lumber", "quotes@gclumber.example.com"),
        ("Southwest Concrete", "estimating@swconcrete.example.com"),
        ("Lone Star Equipment", "bids@lonestarequip.example.com"),
        ("Premier Plumbing Supply", "sales@premierplumb.example.com"),
        ("Metro Electrical", "bids@metroelec.example.com"),
        ("Capitol HVAC", "quotes@capitolhvac.example.com"),
        ("Bayou Paint Co", "sales@bayoupaint.example.com"),
        ("Rio Grande Glass", "estimating@rgglass.example.com"),
        ("Alamo Fasteners", "orders@alamofast.example.com"),
        ("Hill Country Roofing", "bids@hcroofing.example.com"),
        ("Dallas Door & Hardware", "quotes@dallasdoor.example.com"),
        ("Houston Fire Protection", "bids@houstonfp.example.com"),
        ("San Antonio Tile & Stone", "sales@satile.example.com"),
    ]

    for pid in PROJECT_IDS:
        num_pkgs = random.randint(3, 4)
        pkg_trades = random.sample(bid_trades, num_pkgs)
        for trade in pkg_trades:
            bp_count += 1
            bp_status = random.choice(bp_statuses)
            due = date(2025, 3, 15) + timedelta(days=random.randint(0, 45))

            bp = BidPackage(
                company_id=COMPANY_ID,
                project_id=pid,
                sequence_name=f"BP{bp_count:05d}",
                name=f"{trade} Bid Package",
                trade=trade,
                due_date=due,
                status=bp_status,
                description=f"Request for proposals: {trade} scope of work per project specifications.",
            )
            db.add(bp)
            db.flush()

            # Submissions
            num_subs = random.randint(2, 4)
            chosen_vendors = random.sample(VENDORS_BID, num_subs)
            awarded_one = False
            for vendor_name, vendor_email in chosen_vendors:
                bs_count += 1
                sub_status = random.choice(bid_sub_statuses)
                is_awarded = False
                if bp_status == "awarded" and not awarded_one and sub_status in ("submitted", "under_review", "awarded"):
                    sub_status = "awarded"
                    is_awarded = True
                    awarded_one = True
                amt = round(random.uniform(50000, 500000), 2)

                bs = BidSubmission(
                    bid_package_id=bp.id,
                    company_id=COMPANY_ID,
                    vendor_name=vendor_name,
                    vendor_email=vendor_email,
                    status=sub_status,
                    total_amount=amt,
                    scope_description=f"Complete {trade} scope per plans and specifications. Includes all labor, material, and equipment.",
                    submitted_date=due - timedelta(days=random.randint(0, 10)) if sub_status not in ("invited", "draft") else None,
                    is_awarded=is_awarded,
                )
                db.add(bs)

        if pid % 4 == 0:
            db.commit()

    db.commit()
    print(f"  Bid Packages: {bp_count}, Bid Submissions: {bs_count}")

    # --- Portal Configs ---
    pc_count = 0
    for pid in PROJECT_IDS:
        pc_count += 1
        pc = PortalConfig(
            company_id=COMPANY_ID,
            project_id=pid,
            client_portal_enabled=random.random() < 0.85,
            sub_portal_enabled=random.random() < 0.75,
            show_budget=random.random() < 0.4,
            show_schedule=random.random() < 0.9,
            show_documents=random.random() < 0.8,
            show_photos=random.random() < 0.9,
            show_daily_logs=random.random() < 0.3,
            welcome_message=f"Welcome to Project {pid} client portal. Contact your project manager for access questions.",
        )
        db.add(pc)

    db.commit()
    print(f"  Portal Configs: {pc_count}")

    # ===================================================================
    # PHASE 6: agcm_reporting
    # ===================================================================
    print("\n=== Seeding Reporting Data ===")

    # --- Report Definitions & Schedules ---
    rd_count = 0
    rs_count = 0

    REPORT_DEFS = [
        ("Project Financial Summary", "financial", "agcm_projects",
         '["project_name","budget","actual_cost","variance","pct_complete"]',
         '{"status":"active"}'),
        ("Monthly Cost Breakdown", "financial", "agcm_vendor_bills",
         '["vendor_name","bill_number","total_amount","status","due_date"]',
         '{"date_range":"monthly"}'),
        ("Purchase Order Status", "financial", "agcm_purchase_orders",
         '["po_number","vendor_name","total_amount","status","expected_delivery"]',
         '{}'),
        ("Subcontract Progress", "financial", "agcm_subcontracts",
         '["contract_number","vendor_name","revised_amount","billed_to_date","balance_remaining"]',
         '{}'),
        ("Budget vs Actual", "financial", "agcm_estimates",
         '["project_name","estimated_total","actual_total","variance_pct"]',
         '{}'),
        ("Project Schedule Overview", "schedule", "agcm_projects",
         '["project_name","start_date","end_date","pct_complete","status"]',
         '{"status":"active"}'),
        ("Daily Activity Summary", "schedule", "agcm_daily_activity_logs",
         '["project_name","date","weather","manpower_count","notes"]',
         '{"date_range":"weekly"}'),
        ("Safety Inspection Report", "safety", "agcm_safety_inspections",
         '["project_name","inspector_name","inspection_type","status","overall_result","completed_date"]',
         '{}'),
        ("Incident Summary", "safety", "agcm_incident_reports",
         '["project_name","title","severity","status","incident_date","days_lost"]',
         '{}'),
        ("Punch List Status", "safety", "agcm_punch_list_items",
         '["project_name","title","priority","status","trade","due_date"]',
         '{"status":"open,in_progress"}'),
        ("Workforce Utilization", "resource", "agcm_timesheets",
         '["worker_name","project_name","total_hours","total_cost","date_range"]',
         '{"date_range":"weekly"}'),
        ("Equipment Utilization", "resource", "agcm_equipment_assignments",
         '["equipment_name","project_name","total_days","total_cost","assigned_date"]',
         '{}'),
        ("Worker Timesheet Detail", "resource", "agcm_timesheets",
         '["worker_name","date","regular_hours","overtime_hours","total_cost","status"]',
         '{}'),
        ("Bid Comparison Report", "custom", "agcm_bid_submissions",
         '["bid_package","vendor_name","total_amount","status","submitted_date"]',
         '{}'),
        ("Selection Decision Log", "custom", "agcm_selections",
         '["project_name","category","name","status","budget_amount","selected_amount","budget_impact"]',
         '{}'),
    ]

    report_ids = []
    for rname, rtype, dsource, columns, filters in REPORT_DEFS:
        rd_count += 1
        rd = ReportDefinition(
            company_id=COMPANY_ID,
            name=rname,
            description=f"Standard {rtype} report: {rname}",
            report_type=rtype,
            data_source=dsource,
            columns=columns,
            filters=filters,
            is_system=True,
            is_shared=True,
            created_by=USER_ID,
        )
        db.add(rd)
        db.flush()
        report_ids.append(rd.id)

    db.commit()

    # Schedules
    schedule_types = ["daily", "weekly", "weekly", "monthly"]
    formats = ["pdf", "pdf", "excel", "csv"]
    recipients_pool = [
        '["pm@construction.example.com","owner@company.example.com"]',
        '["cfo@company.example.com","accounting@company.example.com"]',
        '["safety@company.example.com","osha@company.example.com"]',
        '["exec@company.example.com"]',
    ]

    for rid in random.sample(report_ids, min(10, len(report_ids))):
        rs_count += 1
        stype = random.choice(schedule_types)
        now = datetime.now(timezone.utc)
        next_run = now + timedelta(days=random.randint(1, 7))

        rs = ReportSchedule(
            report_id=rid,
            company_id=COMPANY_ID,
            schedule_type=stype,
            recipients=random.choice(recipients_pool),
            format=random.choice(formats),
            is_active=random.random() < 0.8,
            next_run=next_run,
        )
        db.add(rs)

    db.commit()
    print(f"  Report Definitions: {rd_count}, Report Schedules: {rs_count}")

    # --- Dashboard Layouts & Widgets ---
    dl_count = 0
    dw_count = 0

    LAYOUTS = [
        ("Executive Overview", "executive", True, [
            ("KPI_CARD", "Active Projects", "agcm_projects", 0, 0, 3, 2),
            ("KPI_CARD", "Total Budget", "agcm_estimates", 3, 0, 3, 2),
            ("KPI_CARD", "Open POs", "agcm_purchase_orders", 6, 0, 3, 2),
            ("KPI_CARD", "Safety Score", "agcm_safety_inspections", 9, 0, 3, 2),
            ("BAR_CHART", "Budget vs Actual by Project", "agcm_estimates", 0, 2, 6, 4),
            ("PIE_CHART", "Project Status Distribution", "agcm_projects", 6, 2, 6, 4),
            ("LINE_CHART", "Monthly Spend Trend", "agcm_vendor_bills", 0, 6, 8, 4),
            ("TABLE", "Recent Incidents", "agcm_incident_reports", 8, 6, 4, 4),
        ]),
        ("Project Manager Dashboard", "project", False, [
            ("KPI_CARD", "My Projects", "agcm_projects", 0, 0, 4, 2),
            ("KPI_CARD", "Open Punch Items", "agcm_punch_list_items", 4, 0, 4, 2),
            ("KPI_CARD", "Pending Inspections", "agcm_safety_inspections", 8, 0, 4, 2),
            ("PROGRESS_CARD", "Project Completion Progress", "agcm_projects", 0, 2, 6, 3),
            ("BAR_CHART", "Manpower by Trade", "agcm_timesheets", 6, 2, 6, 3),
            ("TABLE", "Upcoming Inspections", "agcm_safety_inspections", 0, 5, 6, 4),
            ("STAT_GROUP", "Weekly Resource Summary", "agcm_timesheets", 6, 5, 6, 4),
        ]),
        ("Financial Dashboard", "financial", False, [
            ("KPI_CARD", "Total Committed", "agcm_subcontracts", 0, 0, 3, 2),
            ("KPI_CARD", "Paid to Date", "agcm_vendor_bills", 3, 0, 3, 2),
            ("KPI_CARD", "Outstanding Balance", "agcm_vendor_bills", 6, 0, 3, 2),
            ("KPI_CARD", "Change Orders", "agcm_subcontracts", 9, 0, 3, 2),
            ("LINE_CHART", "Cash Flow Projection", "agcm_vendor_bills", 0, 2, 8, 4),
            ("PIE_CHART", "Cost by Category", "agcm_purchase_orders", 8, 2, 4, 4),
            ("TABLE", "Overdue Bills", "agcm_vendor_bills", 0, 6, 12, 4),
        ]),
        ("Safety Dashboard", "executive", False, [
            ("KPI_CARD", "Total Inspections", "agcm_safety_inspections", 0, 0, 3, 2),
            ("KPI_CARD", "Pass Rate", "agcm_safety_inspections", 3, 0, 3, 2),
            ("KPI_CARD", "Open Incidents", "agcm_incident_reports", 6, 0, 3, 2),
            ("KPI_CARD", "Days Without Incident", "agcm_incident_reports", 9, 0, 3, 2),
            ("BAR_CHART", "Incidents by Severity", "agcm_incident_reports", 0, 2, 6, 4),
            ("LINE_CHART", "Inspection Trend", "agcm_safety_inspections", 6, 2, 6, 4),
            ("TABLE", "Critical Punch Items", "agcm_punch_list_items", 0, 6, 6, 4),
            ("PIE_CHART", "Punch Items by Status", "agcm_punch_list_items", 6, 6, 6, 4),
        ]),
        ("Resource Dashboard", "executive", False, [
            ("KPI_CARD", "Total Workers", "agcm_workers", 0, 0, 3, 2),
            ("KPI_CARD", "Equipment In Use", "agcm_equipment", 3, 0, 3, 2),
            ("KPI_CARD", "Weekly Labor Cost", "agcm_timesheets", 6, 0, 3, 2),
            ("KPI_CARD", "Equipment Cost MTD", "agcm_equipment_assignments", 9, 0, 3, 2),
            ("BAR_CHART", "Workers by Trade", "agcm_workers", 0, 2, 6, 4),
            ("PIE_CHART", "Equipment by Status", "agcm_equipment", 6, 2, 6, 4),
            ("LINE_CHART", "Labor Hours Trend", "agcm_timesheets", 0, 6, 8, 4),
            ("TABLE", "Top Timesheets This Week", "agcm_timesheets", 8, 6, 4, 4),
        ]),
    ]

    for layout_name, layout_type, is_default, widgets in LAYOUTS:
        dl_count += 1
        dl = DashboardLayout(
            company_id=COMPANY_ID,
            name=layout_name,
            layout_type=layout_type,
            is_default=is_default,
            created_by=USER_ID,
        )
        db.add(dl)
        db.flush()

        # Flush layout so dl.id is available
        db.flush()
        for j, (wtype, title, dsource, px, py, w, h) in enumerate(widgets):
            dw_count += 1
            # Insert via raw SQL to bypass Python enum vs DB enum casing mismatch
            db.execute(_text(
                "INSERT INTO agcm_dashboard_widgets "
                "(layout_id, company_id, widget_type, title, data_source, "
                "position_x, position_y, width, height, display_order) "
                "VALUES (:lid, :cid, :wt, :title, :ds, :px, :py, :w, :h, :do)"
            ), {
                "lid": dl.id, "cid": COMPANY_ID, "wt": wtype, "title": title,
                "ds": dsource, "px": px, "py": py, "w": w, "h": h, "do": j,
            })

    db.commit()
    print(f"  Dashboard Layouts: {dl_count}, Dashboard Widgets: {dw_count}")

    # ===================================================================
    # Summary
    # ===================================================================
    from sqlalchemy import text
    tables = [
        # Resource
        "agcm_workers", "agcm_equipment", "agcm_timesheets", "agcm_equipment_assignments",
        # Safety
        "agcm_checklist_templates", "agcm_checklist_template_items",
        "agcm_safety_inspections", "agcm_safety_inspection_items",
        "agcm_punch_list_items", "agcm_incident_reports",
        # Portal
        "agcm_selections", "agcm_selection_options",
        "agcm_bid_packages", "agcm_bid_submissions",
        "agcm_portal_configs",
        # Reporting
        "agcm_report_definitions", "agcm_report_schedules",
        "agcm_dashboard_layouts", "agcm_dashboard_widgets",
    ]
    total = 0
    print(f"\n{'=' * 60}")
    print("PHASES 3-6 SEED SUMMARY")
    print(f"{'=' * 60}")
    for t in tables:
        try:
            c = db.execute(text(f"SELECT count(*) FROM {t}")).scalar()
        except Exception:
            c = 0
        total += c
        print(f"  {t:45s} {c:>6}")
    print(f"  {'─' * 52}")
    print(f"  {'TOTAL':45s} {total:>6}")
    print(f"{'=' * 60}")

    db.close()
    print("Done!")


if __name__ == "__main__":
    seed()
