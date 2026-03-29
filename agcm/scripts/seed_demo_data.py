"""
Seed demo data for AGCM module — realistic construction daily log data.
Run: cd /opt/FastVue/backend && source .venv/bin/activate && ENV_FILE=.env.agcm python -m agcm.scripts.seed_demo_data
"""

import os
import sys
import random
from datetime import date, datetime, timedelta

# Setup paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

os.environ.setdefault('ENV_FILE', '.env.agcm')

from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
db = Session()

COMPANY_ID = 1
USER_ID = 1

# ============================================================================
# Lookup seed data
# ============================================================================

TRADES = [
    "General Contractor", "Electrical", "Plumbing", "HVAC", "Concrete",
    "Structural Steel", "Roofing", "Drywall", "Painting", "Landscaping",
    "Fire Protection", "Masonry", "Flooring", "Glass & Glazing", "Demolition",
]

INSPECTION_TYPES = [
    "Foundation", "Structural", "Electrical", "Plumbing", "HVAC",
    "Fire Safety", "Roofing", "Concrete Pour", "Framing", "Final Walkthrough",
    "Code Compliance", "Environmental", "ADA Compliance", "Elevator", "Waterproofing",
]

ACCIDENT_TYPES = [
    "Fall from Height", "Struck by Object", "Caught Between", "Electrocution",
    "Slip and Trip", "Equipment Malfunction", "Heat Exhaustion", "Chemical Exposure",
    "Vehicle Incident", "Lifting Injury",
]

VIOLATION_TYPES = [
    "PPE Non-Compliance", "Fall Protection", "Scaffolding", "Electrical Hazard",
    "Housekeeping", "Fire Hazard", "Excavation Safety", "Crane Operation",
    "Confined Space", "Noise Exposure",
]

PROJECTS = [
    ("HCESD2 Admin Building", "PRJ-2024-001", "14418 Beaumont Hwy", "Houston", "TX", "77049", "east"),
    ("Memorial City Tower", "PRJ-2024-002", "9800 Memorial Blvd", "Houston", "TX", "77024", "east"),
    ("Corpus Christi Marina", "PRJ-2024-003", "600 N Shoreline Blvd", "Corpus Christi", "TX", "78401", "south"),
    ("San Antonio Medical Center", "PRJ-2024-004", "7703 Floyd Curl Dr", "San Antonio", "TX", "78229", "central"),
    ("Dallas Convention Center", "PRJ-2024-005", "650 S Griffin St", "Dallas", "TX", "75202", "north"),
    ("Katy Freeway Office Park", "PRJ-2024-006", "1800 West Loop S", "Houston", "TX", "77027", "east"),
    ("Austin Tech Campus", "PRJ-2024-007", "3500 Bee Cave Rd", "Austin", "TX", "78746", "central"),
    ("Fort Worth Warehouse", "PRJ-2024-008", "4200 Meacham Blvd", "Fort Worth", "TX", "76137", "north"),
    ("Galveston Beach Resort", "PRJ-2024-009", "3228 Seawall Blvd", "Galveston", "TX", "77550", "east"),
    ("El Paso Distribution Hub", "PRJ-2024-010", "8001 Gateway Blvd", "El Paso", "TX", "79925", "central"),
]

CONTRACTOR_NAMES = [
    "Durotech", "Diversified Plastic Inc.", "Texas Electrical Solutions",
    "Maldonado Landscaping", "Gulf Coast Plumbing", "Lone Star HVAC",
    "Premier Steel Erectors", "Southwest Concrete", "Hill Country Roofing",
    "Alamo Fire Protection", "Capitol Masonry", "Metro Glass & Glazing",
    "Texas Demolition Co.", "Rio Grande Flooring", "Bayou Painting LLC",
]

MANPOWER_COMMENTS = [
    "Concrete pouring crew", "Electrical rough-in", "Plumbing installation",
    "HVAC ductwork", "Structural steel erection", "Drywall hanging",
    "Exterior painting", "Landscaping crew", "Fire sprinkler installation",
    "Roofing crew", "Masonry work", "Flooring installation",
    "Window installation", "Demolition crew", "Excavation work",
    "Framing crew", "Insulation installation", "Tile work",
    "Elevator installation", "Waterproofing application",
]

NOTES_COMMENTS = [
    "Site and Landscaping", "Canopies and Awnings", "Electrical and Low Voltage",
    "Plumbing and Restrooms", "Drywall, Paint, and Wall Finishes", "Mechanical",
    "Roofing", "Masonry/Plaster", "Doors, Windows, and Storefront",
    "Fire Alarm", "Ceilings", "Meetings", "Concrete Work", "Steel Erection",
    "Elevator Installation", "Waterproofing", "Flooring", "Site Utilities",
    "Parking Lot", "Signage",
]

NOTES_DESCRIPTIONS = [
    "Trenching for landscaping irrigation lines and placing sprinkler nozzles",
    "No progress today", "Final wiring for power to among devices",
    "Restroom trim out beginning today with mirror and grab bar installation",
    "No work observed", "No Progress observed today",
    "Stucco installation ongoing on front, rear, and sides of vehicle storage building",
    "None today", "Concrete pour scheduled for tomorrow",
    "Steel delivery arrived on site", "Elevator shaft framing complete",
    "Waterproofing membrane applied to foundation walls",
    "Tile installation in lobby area", "Underground utilities being connected",
    "Parking lot base course being laid", "Exterior signage brackets installed",
    "Interior painting continues on 2nd floor", "Ductwork installation in progress",
    "Electrical panel installation complete", "Plumbing fixtures being set",
]

LOCATIONS = [
    "Floor 1", "Floor 2", "Floor 3", "Floor 4", "Basement",
    "Lobby", "Exterior North", "Exterior South", "Exterior East", "Exterior West",
    "Parking Garage", "Roof", "Mechanical Room", "Loading Dock", "Courtyard",
    "Conference Room A", "Office Wing", "Elevator Shaft", "Stairwell", "Restroom Area",
]

VISITOR_NAMES = [
    "John Smith", "Maria Garcia", "David Johnson", "Sarah Williams", "Michael Brown",
    "Jennifer Davis", "Robert Miller", "Linda Wilson", "William Moore", "Elizabeth Taylor",
    "James Anderson", "Barbara Thomas", "Richard Jackson", "Susan White", "Joseph Harris",
]

VISITOR_REASONS = [
    "Site inspection", "Material delivery coordination", "Client walkthrough",
    "Engineering review", "Safety audit", "City inspector visit",
    "Architect review", "Subcontractor meeting", "Equipment delivery",
    "Fire marshal inspection", "ADA compliance review", "Environmental assessment",
    "Progress photography", "Quality control review", "Final punch list walkthrough",
]

DELAY_REASONS = [
    "Weather delay - heavy rain", "Material delivery delayed",
    "Equipment breakdown", "Permit not yet approved",
    "Design change requested by owner", "Subcontractor no-show",
    "Concrete cure time required", "Utility conflict discovered",
    "Inspector not available", "Safety stand-down required",
    "Holiday/weekend", "Labor shortage", "Supply chain delay",
    "Site access restricted", "Change order processing",
]

DEFICIENCY_NAMES = [
    "Concrete crack in foundation", "Misaligned door frame",
    "Paint finish defect", "Plumbing leak at joint",
    "Electrical outlet not grounded", "HVAC duct not sealed",
    "Window seal incomplete", "Drywall patch needed",
    "Tile grout missing", "Handrail loose",
    "Fire caulking incomplete", "Waterproofing gap",
    "Floor levelness issue", "Ceiling tile damaged",
    "Signage placement incorrect",
]

SAFETY_DESCRIPTIONS = [
    "Worker without hard hat", "Missing guardrail on scaffold",
    "Electrical cord in walkway", "Unsecured ladder",
    "No safety glasses worn", "Excavation without shoring",
    "Blocked emergency exit", "Missing fire extinguisher",
    "Improperly stored chemicals", "No fall protection at edge",
]

SAFETY_NOTICES = [
    "Verbal warning issued to crew foreman",
    "Written notice sent to subcontractor",
    "Work stopped until corrected",
    "Safety meeting conducted on site",
    "Corrective action required within 24 hours",
]


def seed():
    # Load ALL model files so relationships resolve properly
    import importlib
    base = os.path.join(os.path.dirname(__file__), '..')
    model_files = [
        'lookups', 'project', 'daily_activity_log', 'manpower', 'weather',
        'notes', 'inspection', 'accident', 'visitor', 'safety_violation',
        'delay', 'deficiency', 'photo',
    ]
    mods = {}
    for mf in model_files:
        path = os.path.join(base, 'models', f'{mf}.py')
        spec = importlib.util.spec_from_file_location(f'_agcm_{mf}', path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[f'_agcm_{mf}'] = mod
        spec.loader.exec_module(mod)
        mods[mf] = mod

    Trade = mods['lookups'].Trade
    InspectionType = mods['lookups'].InspectionType
    AccidentType = mods['lookups'].AccidentType
    ViolationType = mods['lookups'].ViolationType
    Project = mods['project'].Project
    agcm_project_users = mods['project'].agcm_project_users
    DailyActivityLog = mods['daily_activity_log'].DailyActivityLog
    ManPower = mods['manpower'].ManPower
    Weather = mods['weather'].Weather
    WeatherForecast = mods['weather'].WeatherForecast
    Notes = mods['notes'].Notes
    Inspection = mods['inspection'].Inspection
    Accident = mods['accident'].Accident
    Visitor = mods['visitor'].Visitor
    SafetyViolation = mods['safety_violation'].SafetyViolation
    Delay = mods['delay'].Delay
    Deficiency = mods['deficiency'].Deficiency

    print("Seeding AGCM demo data...")

    # --- Lookups ---
    print("  Trades...")
    trade_ids = []
    for name in TRADES:
        t = Trade(name=name, company_id=COMPANY_ID)
        db.add(t)
        db.flush()
        trade_ids.append(t.id)

    print("  Inspection Types...")
    insp_type_ids = []
    for name in INSPECTION_TYPES:
        it = InspectionType(name=name, company_id=COMPANY_ID)
        db.add(it)
        db.flush()
        insp_type_ids.append(it.id)

    print("  Accident Types...")
    acc_type_ids = []
    for name in ACCIDENT_TYPES:
        at = AccidentType(name=name, company_id=COMPANY_ID)
        db.add(at)
        db.flush()
        acc_type_ids.append(at.id)

    print("  Violation Types...")
    viol_type_ids = []
    for name in VIOLATION_TYPES:
        vt = ViolationType(name=name, company_id=COMPANY_ID)
        db.add(vt)
        db.flush()
        viol_type_ids.append(vt.id)

    db.commit()

    # --- Projects ---
    print("  Projects...")
    project_ids = []
    for i, (name, ref, street, city, state, zipcode, office) in enumerate(PROJECTS):
        p = Project(
            company_id=COMPANY_ID,
            sequence_name=f"Proj{i+1:05d}",
            name=name,
            ref_number=ref,
            start_date=date(2024, 1, 1) + timedelta(days=i * 30),
            end_date=date(2025, 12, 31),
            status=random.choice(["new", "inprogress", "inprogress", "inprogress", "completed"]),
            trade_id=random.choice(trade_ids),
            owner_id=USER_ID,
            street=street,
            city=city,
            state=state,
            zip=zipcode,
            country="US",
            agcm_office=office,
            project_latitude=round(random.uniform(29.5, 33.5), 4),
            project_longitude=round(random.uniform(-99.0, -95.0), 4),
            created_by=USER_ID,
        )
        db.add(p)
        db.flush()
        project_ids.append(p.id)
        # Add user to project
        db.execute(agcm_project_users.insert().values(project_id=p.id, user_id=USER_ID))

    db.commit()

    # --- Daily Logs (50 per project = 500 total) ---
    print("  Daily Logs (500)...")
    log_ids = []
    log_counter = 0
    for pid in project_ids:
        base_date = date(2026, 1, 1)
        for d in range(50):
            log_date = base_date + timedelta(days=d)
            if log_date.weekday() >= 5:  # skip weekends
                log_date = log_date + timedelta(days=2)
            log_counter += 1
            dl = DailyActivityLog(
                company_id=COMPANY_ID,
                sequence_name=f"DL{log_counter:05d}",
                date=log_date,
                project_id=pid,
                created_by=USER_ID,
            )
            db.add(dl)
            db.flush()
            log_ids.append((dl.id, pid, log_date))

    db.commit()
    print(f"    Created {len(log_ids)} daily logs")

    # --- Weather Forecasts (6 per log for first 100 logs) ---
    print("  Weather Forecasts...")
    wf_count = 0
    for log_id, pid, log_date in log_ids[:100]:
        for hour in [6, 9, 12, 15, 18, 21]:
            code = random.choices([1, 1, 1, 2, 2, 3, 4, 5], weights=[30, 20, 10, 15, 10, 8, 5, 2])[0]
            wf = WeatherForecast(
                company_id=COMPANY_ID,
                date=log_date,
                time_interval=f"{log_date}T{hour:02d}:00",
                temperature=random.randint(55, 98),
                humidity=random.randint(30, 90),
                wind=round(random.uniform(2, 25), 1),
                precipitation=round(random.uniform(0, 0.5), 2) if code >= 3 else 0,
                weather_code=code,
                dailylog_id=log_id,
                project_id=pid,
            )
            db.add(wf)
            wf_count += 1

    db.commit()
    print(f"    Created {wf_count} weather forecast entries")

    # --- Manual Weather (1-2 per log for first 200 logs) ---
    print("  Manual Weather...")
    mw_count = 0
    for log_id, pid, log_date in log_ids[:200]:
        for _ in range(random.randint(1, 2)):
            mw_count += 1
            w = Weather(
                company_id=COMPANY_ID,
                sequence_name=f"Weather{mw_count:05d}",
                date=log_date,
                temperature=random.randint(60, 100),
                temperature_type="F",
                climate_type=random.choice(["clear", "cloudy", "wet", "dry"]),
                humidity=random.randint(30, 85),
                wind=round(random.uniform(3, 20), 1),
                precipitation=round(random.uniform(0, 1.5), 2),
                rain=random.choice([False, False, False, True]),
                rain_fall=round(random.uniform(0, 0.8), 2),
                dailylog_id=log_id,
                project_id=pid,
            )
            db.add(w)

    db.commit()
    print(f"    Created {mw_count} manual weather entries")

    # --- Manpower (500+ entries, 1-3 per log) ---
    print("  Manpower (500+)...")
    mp_count = 0
    for log_id, pid, log_date in log_ids:
        for _ in range(random.randint(1, 3)):
            mp_count += 1
            workers = random.randint(2, 15)
            hours = round(random.choice([4.0, 6.0, 8.0, 10.0, 12.0]), 1)
            mp = ManPower(
                company_id=COMPANY_ID,
                sequence_name=f"MP{mp_count:05d}",
                name=random.choice(MANPOWER_COMMENTS),
                location=random.choice(LOCATIONS),
                number_of_workers=workers,
                number_of_hours=hours,
                total_hours=workers * hours,
                dailylog_id=log_id,
                project_id=pid,
                created_by=USER_ID,
            )
            db.add(mp)
        if mp_count % 200 == 0:
            db.commit()

    db.commit()
    print(f"    Created {mp_count} manpower entries")

    # --- Notes (500+ entries) ---
    print("  Notes/Observations (500+)...")
    note_count = 0
    for log_id, pid, log_date in log_ids:
        for _ in range(random.randint(1, 3)):
            note_count += 1
            n = Notes(
                company_id=COMPANY_ID,
                sequence_name=f"Observations{note_count:05d}",
                name=random.choice(NOTES_COMMENTS),
                description=random.choice(NOTES_DESCRIPTIONS),
                location=random.choice(LOCATIONS),
                dailylog_id=log_id,
                project_id=pid,
                created_by=USER_ID,
            )
            db.add(n)
        if note_count % 200 == 0:
            db.commit()

    db.commit()
    print(f"    Created {note_count} notes")

    # --- Inspections (500+) ---
    print("  Inspections (500+)...")
    insp_count = 0
    for log_id, pid, log_date in log_ids:
        if random.random() < 0.6:  # 60% of logs have inspections
            insp_count += 1
            i = Inspection(
                company_id=COMPANY_ID,
                sequence_name=f"Inspection{insp_count:05d}",
                name=f"Inspection #{insp_count}",
                inspection_type_id=random.choice(insp_type_ids),
                result=random.choice(["Pass", "Pass", "Pass", "Fail", "Conditional Pass", "Re-inspection Required"]),
                dailylog_id=log_id,
                project_id=pid,
                created_by=USER_ID,
            )
            db.add(i)
        if insp_count % 200 == 0:
            db.commit()

    db.commit()
    print(f"    Created {insp_count} inspections")

    # --- Visitors (500+) ---
    print("  Visitors (500+)...")
    vis_count = 0
    for log_id, pid, log_date in log_ids:
        if random.random() < 0.7:
            vis_count += 1
            entry_hour = random.randint(7, 14)
            exit_hour = entry_hour + random.randint(1, 4)
            v = Visitor(
                company_id=COMPANY_ID,
                sequence_name=f"Visitor{vis_count:05d}",
                name=random.choice(VISITOR_NAMES),
                reason=random.choice(VISITOR_REASONS),
                visit_entry_time=datetime.combine(log_date, datetime.min.time()).replace(hour=entry_hour, minute=random.randint(0, 59)),
                visit_exit_time=datetime.combine(log_date, datetime.min.time()).replace(hour=exit_hour, minute=random.randint(0, 59)),
                comments=random.choice(["", "", "Escorted by PM", "Badge issued", "Hard hat provided"]),
                dailylog_id=log_id,
                project_id=pid,
                created_by=USER_ID,
            )
            db.add(v)
        if vis_count % 200 == 0:
            db.commit()

    db.commit()
    print(f"    Created {vis_count} visitors")

    # --- Safety Violations (200+) ---
    print("  Safety Observations...")
    sv_count = 0
    for log_id, pid, log_date in log_ids:
        if random.random() < 0.25:
            sv_count += 1
            sv = SafetyViolation(
                company_id=COMPANY_ID,
                sequence_name=f"SV{sv_count:05d}",
                name=random.choice(SAFETY_DESCRIPTIONS),
                violation_notice=random.choice(SAFETY_NOTICES),
                violation_type_id=random.choice(viol_type_ids),
                dailylog_id=log_id,
                project_id=pid,
                created_by=USER_ID,
            )
            db.add(sv)
        if sv_count % 200 == 0:
            db.commit()

    db.commit()
    print(f"    Created {sv_count} safety observations")

    # --- Delays (200+) ---
    print("  Delays...")
    delay_count = 0
    for log_id, pid, log_date in log_ids:
        if random.random() < 0.2:
            delay_count += 1
            d = Delay(
                company_id=COMPANY_ID,
                sequence_name=f"Delay{delay_count:05d}",
                name=f"Delay #{delay_count}",
                reason=random.choice(DELAY_REASONS),
                delay=f"{random.randint(1, 8)} hours lost",
                reported_by=random.choice(VISITOR_NAMES),
                partner_id=USER_ID,
                dailylog_id=log_id,
                project_id=pid,
                created_by=USER_ID,
            )
            db.add(d)
        if delay_count % 200 == 0:
            db.commit()

    db.commit()
    print(f"    Created {delay_count} delays")

    # --- Deficiencies (200+) ---
    print("  Deficiencies...")
    def_count = 0
    for log_id, pid, log_date in log_ids:
        if random.random() < 0.2:
            def_count += 1
            df = Deficiency(
                company_id=COMPANY_ID,
                sequence_name=f"DEF{def_count:05d}",
                name=random.choice(DEFICIENCY_NAMES),
                description=f"Found at {random.choice(LOCATIONS)}. Requires attention within {random.randint(1, 14)} days.",
                dailylog_id=log_id,
                project_id=pid,
                created_by=USER_ID,
            )
            db.add(df)
        if def_count % 200 == 0:
            db.commit()

    db.commit()
    print(f"    Created {def_count} deficiencies")

    # --- Accidents (50+) ---
    print("  Accidents...")
    acc_count = 0
    for log_id, pid, log_date in log_ids:
        if random.random() < 0.05:
            acc_count += 1
            a = Accident(
                company_id=COMPANY_ID,
                sequence_name=f"ACC{acc_count:05d}",
                name=f"Incident: {random.choice(ACCIDENT_TYPES).lower()} reported",
                accident_type_id=random.choice(acc_type_ids),
                resolution=random.choice([
                    "First aid administered", "Worker sent to clinic",
                    "No injury, near miss documented", "Area secured and reviewed",
                    "Equipment taken out of service", "Investigation ongoing",
                ]),
                incident_time=datetime.combine(log_date, datetime.min.time()).replace(
                    hour=random.randint(7, 16), minute=random.randint(0, 59)
                ),
                location=random.choice(LOCATIONS),
                safety_measure_precautions=random.choice([True, True, False]),
                dailylog_id=log_id,
                project_id=pid,
                created_by=USER_ID,
            )
            db.add(a)

    db.commit()
    print(f"    Created {acc_count} accidents")

    # --- Photos (500+ with generated placeholder images) ---
    print("  Photos (500+)...")
    from agcm.scripts._generate_photos import generate_photos
    photo_count = generate_photos(db, log_ids, COMPANY_ID, USER_ID, LOCATIONS)

    print("\n=== DEMO DATA SUMMARY ===")
    print(f"  Trades:              {len(TRADES)}")
    print(f"  Inspection Types:    {len(INSPECTION_TYPES)}")
    print(f"  Accident Types:      {len(ACCIDENT_TYPES)}")
    print(f"  Violation Types:     {len(VIOLATION_TYPES)}")
    print(f"  Projects:            {len(project_ids)}")
    print(f"  Daily Logs:          {len(log_ids)}")
    print(f"  Weather Forecasts:   {wf_count}")
    print(f"  Manual Weather:      {mw_count}")
    print(f"  Manpower:            {mp_count}")
    print(f"  Notes:               {note_count}")
    print(f"  Inspections:         {insp_count}")
    print(f"  Visitors:            {vis_count}")
    print(f"  Safety Observations: {sv_count}")
    print(f"  Delays:              {delay_count}")
    print(f"  Deficiencies:        {def_count}")
    print(f"  Accidents:           {acc_count}")
    print(f"  Photos:              {photo_count}")
    print("========================")
    print("Done!")


if __name__ == "__main__":
    seed()
