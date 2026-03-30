"""
Seed demo data for the agcm_estimate module — cost catalogs, assemblies, estimates, proposals, takeoffs.
Run: cd /opt/FastVue/agcm_addons && python scripts/seed_estimate_data.py

Assumes:
  - COMPANY_ID=1 and USER_ID=1 already exist
  - Projects with IDs 1-12 already exist
  - All agcm_estimate_* tables already exist (auto-created by AutoSchemaManager)
"""

import os
import sys
import random
import importlib.util
from datetime import date, datetime, timedelta

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ.setdefault('ENV_FILE', '.env.agcm')

from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
db = Session()

COMPANY_ID = 1
USER_ID = 1
PROJECT_IDS = list(range(1, 13))  # projects 1-12

# ---------------------------------------------------------------------------
# Helper to load model file by absolute path
# ---------------------------------------------------------------------------
_loaded = {}


def load_model(module_name, file_path):
    """Load a model .py file via importlib.util and cache it."""
    if module_name in _loaded:
        return _loaded[module_name]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    _loaded[module_name] = mod
    return mod


ADDONS_DIR = os.path.join(os.path.dirname(__file__), '..')


def model_path(module, filename):
    return os.path.abspath(os.path.join(ADDONS_DIR, module, 'models', filename))


# ---------------------------------------------------------------------------
# Realistic data
# ---------------------------------------------------------------------------

GENERAL_MATERIALS = [
    ("Ready-Mix Concrete 4000 PSI", "cy", 145.00, "03-100", "Central Concrete", True),
    ("Ready-Mix Concrete 3000 PSI", "cy", 130.00, "03-100", "Central Concrete", True),
    ("Rebar #4 Grade 60", "ton", 850.00, "03-200", "Steel Depot", True),
    ("Rebar #5 Grade 60", "ton", 870.00, "03-200", "Steel Depot", True),
    ("Wire Mesh 6x6 W1.4/W1.4", "sf", 0.35, "03-200", "Steel Depot", True),
    ("Form Lumber 2x4 SPF", "bf", 0.65, "03-110", "Lumber Yard Pro", True),
    ("Form Lumber 2x6 SPF", "bf", 0.85, "03-110", "Lumber Yard Pro", True),
    ("Plywood CDX 3/4\"", "sf", 1.95, "03-110", "Lumber Yard Pro", True),
    ("OSB Sheathing 7/16\"", "sf", 0.95, "06-100", "Lumber Yard Pro", True),
    ("Structural Steel W8x31", "ton", 2200.00, "05-100", "Nucor Steel", True),
    ("Structural Steel W10x49", "ton", 2350.00, "05-100", "Nucor Steel", True),
    ("Steel Studs 3-5/8\" 20ga", "lf", 1.25, "05-400", "ClarkDietrich", True),
    ("Steel Studs 6\" 20ga", "lf", 1.65, "05-400", "ClarkDietrich", True),
    ("Drywall 1/2\" Regular", "sf", 0.42, "09-250", "USG Corp", True),
    ("Drywall 5/8\" Type X Fire", "sf", 0.58, "09-250", "USG Corp", True),
    ("Joint Compound (5 gal)", "ea", 14.50, "09-250", "USG Corp", True),
    ("Drywall Tape 500ft", "ea", 4.75, "09-250", "USG Corp", True),
    ("Interior Latex Paint", "gal", 38.00, "09-910", "Sherwin-Williams", True),
    ("Exterior Latex Paint", "gal", 45.00, "09-910", "Sherwin-Williams", True),
    ("Primer Sealer", "gal", 28.00, "09-910", "Sherwin-Williams", True),
    ("Ceramic Floor Tile 12x12", "sf", 3.25, "09-300", "Daltile", True),
    ("Porcelain Wall Tile 6x6", "sf", 4.50, "09-300", "Daltile", True),
    ("Thin-set Mortar 50lb", "bag", 12.50, "09-300", "Custom Building", True),
    ("Grout Sanded 25lb", "bag", 18.00, "09-300", "Custom Building", True),
    ("Roofing Shingles Architectural", "sq", 95.00, "07-310", "GAF Materials", True),
    ("Roofing Felt 30lb", "roll", 22.00, "07-310", "GAF Materials", True),
    ("TPO Membrane 60mil", "sf", 1.85, "07-540", "Carlisle", True),
    ("Insulation R-19 Batt", "sf", 0.75, "07-210", "Owens Corning", True),
    ("Insulation R-30 Batt", "sf", 1.10, "07-210", "Owens Corning", True),
    ("Rigid Foam 2\" XPS", "sf", 1.45, "07-210", "Dow Chemical", True),
    ("PVC Pipe 4\" Sch40", "lf", 4.25, "15-100", "Charlotte Pipe", True),
    ("Copper Pipe 3/4\" Type L", "lf", 6.50, "15-100", "Mueller", True),
    ("CPVC Pipe 1\"", "lf", 3.75, "15-100", "Charlotte Pipe", True),
    ("EMT Conduit 3/4\"", "lf", 1.85, "16-100", "Allied Tube", True),
    ("Romex 12/2 NM-B", "lf", 0.45, "16-100", "Southwire", True),
    ("THHN Wire #10", "lf", 0.65, "16-100", "Southwire", True),
    ("Concrete Block 8x8x16", "ea", 2.15, "04-200", "Oldcastle APG", True),
    ("Mortar Mix Type S", "bag", 8.50, "04-200", "Quikrete", True),
    ("Anchor Bolts 1/2\"x10\"", "ea", 3.25, "05-500", "Simpson Strong-Tie", True),
    ("Structural Screws #10x3\"", "lb", 4.50, "05-500", "GRK Fasteners", True),
]

LABOR_RATES = [
    ("Electrician Journeyman", "hr", 72.00, "16-010", None, False),
    ("Electrician Apprentice", "hr", 42.00, "16-010", None, False),
    ("Plumber Journeyman", "hr", 75.00, "15-010", None, False),
    ("Plumber Apprentice", "hr", 40.00, "15-010", None, False),
    ("Carpenter Journeyman", "hr", 65.00, "06-010", None, False),
    ("Carpenter Apprentice", "hr", 38.00, "06-010", None, False),
    ("General Laborer", "hr", 32.00, "01-010", None, False),
    ("Skilled Laborer", "hr", 38.00, "01-010", None, False),
    ("Foreman", "hr", 78.00, "01-010", None, False),
    ("Superintendent", "hr", 95.00, "01-010", None, False),
    ("Ironworker Journeyman", "hr", 82.00, "05-010", None, False),
    ("Ironworker Apprentice", "hr", 48.00, "05-010", None, False),
    ("Mason Journeyman", "hr", 68.00, "04-010", None, False),
    ("Mason Apprentice", "hr", 36.00, "04-010", None, False),
    ("Painter Journeyman", "hr", 55.00, "09-010", None, False),
    ("Painter Apprentice", "hr", 32.00, "09-010", None, False),
    ("Sheet Metal Worker", "hr", 70.00, "15-010", None, False),
    ("HVAC Technician", "hr", 74.00, "15-010", None, False),
    ("Roofer Journeyman", "hr", 58.00, "07-010", None, False),
    ("Tile Setter Journeyman", "hr", 62.00, "09-010", None, False),
    ("Concrete Finisher", "hr", 60.00, "03-010", None, False),
    ("Equipment Operator Heavy", "hr", 68.00, "01-010", None, False),
    ("Equipment Operator Light", "hr", 52.00, "01-010", None, False),
    ("Welder Certified", "hr", 78.00, "05-010", None, False),
    ("Insulation Worker", "hr", 48.00, "07-010", None, False),
    ("Drywall Hanger", "hr", 55.00, "09-010", None, False),
    ("Drywall Finisher", "hr", 58.00, "09-010", None, False),
    ("Floor Layer", "hr", 56.00, "09-010", None, False),
    ("Glazier", "hr", 65.00, "08-010", None, False),
    ("Safety Officer", "hr", 85.00, "01-010", None, False),
]

EQUIPMENT_RENTAL = [
    ("Excavator CAT 320", "day", 850.00, "01-500", "United Rentals", True),
    ("Excavator CAT 330", "day", 1100.00, "01-500", "United Rentals", True),
    ("Backhoe Loader CAT 420", "day", 450.00, "01-500", "United Rentals", True),
    ("Skid Steer Bobcat S650", "day", 325.00, "01-500", "Sunbelt Rentals", True),
    ("Crawler Crane 100-ton", "day", 3500.00, "01-500", "Maxim Crane", True),
    ("Mobile Crane 50-ton", "day", 2200.00, "01-500", "Maxim Crane", True),
    ("Telescopic Forklift 10K", "day", 550.00, "01-500", "Sunbelt Rentals", True),
    ("Forklift 5000lb Warehouse", "day", 175.00, "01-500", "Toyota Material", True),
    ("Concrete Pump Truck 42m", "day", 2800.00, "03-500", "Putzmeister", True),
    ("Concrete Vibrator", "day", 65.00, "03-500", "Sunbelt Rentals", True),
    ("Plate Compactor 5000lb", "day", 125.00, "01-500", "United Rentals", True),
    ("Roller Vibratory 66\"", "day", 425.00, "01-500", "United Rentals", True),
    ("Generator 20KW Portable", "day", 185.00, "01-500", "Sunbelt Rentals", True),
    ("Generator 100KW Towable", "day", 450.00, "01-500", "Sunbelt Rentals", True),
    ("Aerial Lift Scissor 26ft", "day", 225.00, "01-500", "United Rentals", True),
    ("Aerial Lift Boom 60ft", "day", 550.00, "01-500", "United Rentals", True),
    ("Dump Truck 10-Wheel", "day", 650.00, "01-500", "Local Hauling Co", True),
    ("Water Truck 4000gal", "day", 500.00, "01-500", "Local Hauling Co", True),
    ("Compressor Air 185CFM", "day", 175.00, "01-500", "Sunbelt Rentals", True),
    ("Welder Lincoln SA-200", "day", 125.00, "05-500", "United Rentals", True),
    ("Scaffolding System (per section)", "day", 35.00, "01-500", "Safway", True),
    ("Concrete Mixer 9cf", "day", 95.00, "03-500", "United Rentals", True),
    ("Trench Box 8x20", "day", 125.00, "01-500", "Trench Plate Rental", True),
    ("Dewatering Pump 6\"", "day", 275.00, "01-500", "Sunbelt Rentals", True),
    ("Survey Equipment Total Station", "day", 185.00, "01-500", "Topcon", True),
    ("Laser Level Rotary", "day", 85.00, "01-500", "Spectra Precision", True),
    ("Light Tower 6KW", "day", 95.00, "01-500", "Sunbelt Rentals", True),
    ("Jackhammer Electric 65lb", "day", 75.00, "01-500", "United Rentals", True),
    ("Concrete Saw Walk-Behind", "day", 165.00, "03-500", "Sunbelt Rentals", True),
    ("Power Trowel 36\"", "day", 110.00, "03-500", "United Rentals", True),
]

ASSEMBLY_DEFS = [
    ("Foundation Package", "Foundation", [
        ("Ready-Mix Concrete 4000 PSI", "material", 25, "cy", 145.00, 5),
        ("Rebar #4 Grade 60", "material", 3, "ton", 850.00, 10),
        ("Wire Mesh 6x6 W1.4/W1.4", "material", 2000, "sf", 0.35, 5),
        ("Form Lumber 2x4 SPF", "material", 800, "bf", 0.65, 15),
        ("Concrete Finisher", "labor", 80, "hr", 60.00, 0),
        ("General Laborer", "labor", 120, "hr", 32.00, 0),
        ("Concrete Pump Truck 42m", "equipment", 3, "day", 2800.00, 0),
    ]),
    ("Framing Package", "Structural", [
        ("Form Lumber 2x4 SPF", "material", 5000, "bf", 0.65, 8),
        ("Form Lumber 2x6 SPF", "material", 3000, "bf", 0.85, 8),
        ("Plywood CDX 3/4\"", "material", 4000, "sf", 1.95, 5),
        ("OSB Sheathing 7/16\"", "material", 6000, "sf", 0.95, 5),
        ("Carpenter Journeyman", "labor", 200, "hr", 65.00, 0),
        ("Carpenter Apprentice", "labor", 160, "hr", 38.00, 0),
    ]),
    ("Electrical Rough-In", "MEP", [
        ("EMT Conduit 3/4\"", "material", 1500, "lf", 1.85, 10),
        ("Romex 12/2 NM-B", "material", 3000, "lf", 0.45, 10),
        ("THHN Wire #10", "material", 2000, "lf", 0.65, 10),
        ("Electrician Journeyman", "labor", 160, "hr", 72.00, 0),
        ("Electrician Apprentice", "labor", 160, "hr", 42.00, 0),
    ]),
    ("Plumbing Rough-In", "MEP", [
        ("PVC Pipe 4\" Sch40", "material", 500, "lf", 4.25, 10),
        ("Copper Pipe 3/4\" Type L", "material", 800, "lf", 6.50, 10),
        ("CPVC Pipe 1\"", "material", 600, "lf", 3.75, 10),
        ("Plumber Journeyman", "labor", 120, "hr", 75.00, 0),
        ("Plumber Apprentice", "labor", 120, "hr", 40.00, 0),
    ]),
    ("HVAC Package", "MEP", [
        ("Sheet Metal Worker", "labor", 160, "hr", 70.00, 0),
        ("HVAC Technician", "labor", 120, "hr", 74.00, 0),
        ("General Laborer", "labor", 80, "hr", 32.00, 0),
        ("Insulation R-19 Batt", "material", 3000, "sf", 0.75, 5),
        ("Aerial Lift Scissor 26ft", "equipment", 10, "day", 225.00, 0),
    ]),
    ("Roofing Package", "Exterior", [
        ("Roofing Shingles Architectural", "material", 40, "sq", 95.00, 5),
        ("Roofing Felt 30lb", "material", 20, "roll", 22.00, 5),
        ("Roofer Journeyman", "labor", 120, "hr", 58.00, 0),
        ("General Laborer", "labor", 80, "hr", 32.00, 0),
        ("Aerial Lift Boom 60ft", "equipment", 5, "day", 550.00, 0),
    ]),
    ("Interior Finish", "Finishes", [
        ("Drywall 1/2\" Regular", "material", 8000, "sf", 0.42, 8),
        ("Drywall 5/8\" Type X Fire", "material", 2000, "sf", 0.58, 8),
        ("Joint Compound (5 gal)", "material", 40, "ea", 14.50, 5),
        ("Interior Latex Paint", "material", 60, "gal", 38.00, 5),
        ("Drywall Hanger", "labor", 120, "hr", 55.00, 0),
        ("Drywall Finisher", "labor", 100, "hr", 58.00, 0),
        ("Painter Journeyman", "labor", 80, "hr", 55.00, 0),
    ]),
    ("Exterior Cladding", "Exterior", [
        ("Steel Studs 6\" 20ga", "material", 3000, "lf", 1.65, 8),
        ("Rigid Foam 2\" XPS", "material", 4000, "sf", 1.45, 5),
        ("Insulation R-30 Batt", "material", 4000, "sf", 1.10, 5),
        ("Carpenter Journeyman", "labor", 100, "hr", 65.00, 0),
        ("Glazier", "labor", 60, "hr", 65.00, 0),
    ]),
    ("Site Work", "Site", [
        ("Excavator CAT 320", "equipment", 10, "day", 850.00, 0),
        ("Dump Truck 10-Wheel", "equipment", 8, "day", 650.00, 0),
        ("Plate Compactor 5000lb", "equipment", 5, "day", 125.00, 0),
        ("Equipment Operator Heavy", "labor", 80, "hr", 68.00, 0),
        ("General Laborer", "labor", 120, "hr", 32.00, 0),
    ]),
    ("Concrete Flatwork", "Concrete", [
        ("Ready-Mix Concrete 3000 PSI", "material", 50, "cy", 130.00, 5),
        ("Wire Mesh 6x6 W1.4/W1.4", "material", 5000, "sf", 0.35, 5),
        ("Concrete Finisher", "labor", 60, "hr", 60.00, 0),
        ("General Laborer", "labor", 80, "hr", 32.00, 0),
        ("Concrete Saw Walk-Behind", "equipment", 3, "day", 165.00, 0),
        ("Power Trowel 36\"", "equipment", 5, "day", 110.00, 0),
    ]),
]

ESTIMATE_GROUPS = ["Foundation", "Structural", "MEP", "Finishes", "Site Work"]

ESTIMATE_NAMES = [
    "Base Building Estimate", "Tenant Improvement Estimate",
    "Site Development Estimate", "Interior Renovation Estimate",
    "Addition & Remodel Estimate",
]

CLIENT_NAMES = [
    "Apex Development Group", "Meridian Properties LLC", "Summit Construction Partners",
    "Coastal Ventures Inc.", "Heritage Building Co.", "Pacific Rim Developers",
    "Ironwood Capital", "Cornerstone Holdings", "Pinnacle Real Estate Group",
    "Greenfield Investments", "Atlas Property Management", "Skyline Development Corp",
]

TAKEOFF_SHEET_NAMES = [
    "Floor Plan Level 1", "Floor Plan Level 2", "Floor Plan Level 3",
    "Site Plan", "Foundation Plan", "Roof Plan",
    "Elevation North", "Elevation South", "Elevation East", "Elevation West",
    "Section A-A", "Section B-B", "Reflected Ceiling Plan",
    "Mechanical Plan", "Electrical Plan", "Plumbing Plan",
]

MEASUREMENT_LABELS = [
    "Exterior Wall", "Interior Partition", "Foundation Slab",
    "Floor Area Level 1", "Floor Area Level 2", "Roof Area",
    "Window Opening", "Door Opening", "Stairwell",
    "Corridor Length", "Pipe Run Kitchen", "Duct Run Main",
    "Concrete Pour Area", "Tile Floor Restroom", "Paint Wall Area",
    "Ceiling Grid Area", "Parking Lot Area", "Sidewalk Length",
    "Curb Length", "Fence Line", "Landscape Area",
    "Excavation Area", "Footing Perimeter", "Column Count",
    "Outlet Count", "Fixture Count", "Sprinkler Head Count",
]


# ============================================================================
# SEED FUNCTION
# ============================================================================

def seed():
    random.seed(42)

    print("=" * 60)
    print("SEEDING AGCM ESTIMATE MODULE")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Load model files
    # ------------------------------------------------------------------
    print("\nLoading model files...")

    # Base agcm models (needed for FK references)
    base_agcm_models = [
        'lookups', 'project', 'daily_activity_log', 'manpower', 'weather',
        'notes', 'inspection', 'accident', 'visitor', 'safety_violation',
        'delay', 'deficiency', 'photo',
    ]
    for mf in base_agcm_models:
        load_model(f'_agcm_base_{mf}', model_path('agcm', f'{mf}.py'))

    try:
        from app.models import User, Company  # noqa: F401
    except Exception:
        pass

    # Estimate module models
    mod_cost_catalog = load_model('_est_cost_catalog', model_path('agcm_estimate', 'cost_catalog.py'))
    mod_assembly = load_model('_est_assembly', model_path('agcm_estimate', 'assembly.py'))
    mod_estimate = load_model('_est_estimate', model_path('agcm_estimate', 'estimate.py'))
    mod_markup = load_model('_est_markup', model_path('agcm_estimate', 'estimate_markup.py'))
    mod_proposal = load_model('_est_proposal', model_path('agcm_estimate', 'proposal.py'))
    mod_takeoff = load_model('_est_takeoff', model_path('agcm_estimate', 'takeoff.py'))

    CostCatalog = mod_cost_catalog.CostCatalog
    CostItem = mod_cost_catalog.CostItem
    ItemType = mod_cost_catalog.ItemType
    Assembly = mod_assembly.Assembly
    AssemblyItem = mod_assembly.AssemblyItem
    Estimate = mod_estimate.Estimate
    EstimateGroup = mod_estimate.EstimateGroup
    EstimateLineItem = mod_estimate.EstimateLineItem
    EstimateStatus = mod_estimate.EstimateStatus
    LineItemType = mod_estimate.LineItemType
    EstimateMarkup = mod_markup.EstimateMarkup
    MarkupType = mod_markup.MarkupType
    Proposal = mod_proposal.Proposal
    ProposalStatus = mod_proposal.ProposalStatus
    TakeoffSheet = mod_takeoff.TakeoffSheet
    TakeoffMeasurement = mod_takeoff.TakeoffMeasurement
    MeasurementType = mod_takeoff.MeasurementType

    counts = {}

    # ==================================================================
    # COST CATALOGS (3 catalogs, 100 items)
    # ==================================================================
    print("\n--- Cost Catalogs ---")

    item_type_map = {
        "material": ItemType.MATERIAL,
        "labor": ItemType.LABOR,
        "equipment": ItemType.EQUIPMENT,
        "subcontractor": ItemType.SUBCONTRACTOR,
        "fee": ItemType.FEE,
        "other": ItemType.OTHER,
    }

    all_cost_items = []  # track for use in estimates
    catalog_map = {}     # name -> catalog obj

    catalog_defs = [
        ("General Materials", "Common construction materials and supplies", GENERAL_MATERIALS, "material"),
        ("Labor Rates", "Trade labor rates for all disciplines", LABOR_RATES, "labor"),
        ("Equipment Rental", "Equipment and tool rental rates", EQUIPMENT_RENTAL, "equipment"),
    ]

    for cat_name, cat_desc, items_list, default_type in catalog_defs:
        catalog = CostCatalog(
            company_id=COMPANY_ID,
            name=cat_name,
            description=cat_desc,
            is_default=(cat_name == "General Materials"),
        )
        db.add(catalog)
        db.flush()
        catalog_map[cat_name] = catalog

        for name, unit, unit_cost, cost_code, vendor, taxable in items_list:
            markup_factor = random.uniform(1.2, 1.5)
            item = CostItem(
                company_id=COMPANY_ID,
                catalog_id=catalog.id,
                name=name,
                item_type=item_type_map[default_type],
                unit=unit,
                unit_cost=unit_cost,
                unit_price=round(unit_cost * markup_factor, 2),
                taxable=taxable,
                cost_code=cost_code,
                vendor=vendor,
                category=cat_name,
                is_active=True,
            )
            db.add(item)
            all_cost_items.append(item)

        db.flush()
        print(f"  {cat_name}: {len(items_list)} items")

    counts["cost_catalogs"] = 3
    counts["cost_items"] = len(all_cost_items)

    # ==================================================================
    # ASSEMBLIES (10 assemblies, 50+ items)
    # ==================================================================
    print("\n--- Assemblies ---")

    assembly_item_count = 0
    assembly_objs = []

    for asm_name, asm_category, asm_items in ASSEMBLY_DEFS:
        assembly = Assembly(
            company_id=COMPANY_ID,
            name=asm_name,
            description=f"Standard {asm_name.lower()} for typical commercial construction",
            category=asm_category,
            is_active=True,
        )
        db.add(assembly)
        db.flush()
        assembly_objs.append(assembly)

        for item_name, item_type_str, qty, unit, cost, waste in asm_items:
            # Try to find a matching cost item
            matching = [ci for ci in all_cost_items if ci.name == item_name]
            cost_item_id = matching[0].id if matching else None

            ai = AssemblyItem(
                assembly_id=assembly.id,
                company_id=COMPANY_ID,
                cost_item_id=cost_item_id,
                name=item_name,
                item_type=item_type_map.get(item_type_str, ItemType.OTHER),
                quantity=qty,
                unit=unit,
                unit_cost=cost,
                waste_factor=waste,
            )
            db.add(ai)
            assembly_item_count += 1

        db.flush()
        print(f"  {asm_name}: {len(asm_items)} items")

    counts["assemblies"] = len(ASSEMBLY_DEFS)
    counts["assembly_items"] = assembly_item_count

    # ==================================================================
    # ESTIMATES (60+ across 12 projects, 5 per project)
    # ==================================================================
    print("\n--- Estimates ---")

    line_item_type_map = {
        "material": LineItemType.MATERIAL,
        "labor": LineItemType.LABOR,
        "equipment": LineItemType.EQUIPMENT,
        "subcontractor": LineItemType.SUBCONTRACTOR,
        "fee": LineItemType.FEE,
        "allowance": LineItemType.ALLOWANCE,
        "assembly": LineItemType.ASSEMBLY,
    }

    status_weights = [
        (EstimateStatus.DRAFT, 0.40),
        (EstimateStatus.IN_REVIEW, 0.20),
        (EstimateStatus.APPROVED, 0.30),
        (EstimateStatus.REJECTED, 0.10),
    ]

    estimate_count = 0
    group_count = 0
    line_item_count = 0
    all_estimates = []
    all_line_items = []

    est_seq = 1

    for pid in PROJECT_IDS:
        for est_idx in range(5):
            # Pick status based on weights
            r = random.random()
            cumul = 0
            status = EstimateStatus.DRAFT
            for s, w in status_weights:
                cumul += w
                if r <= cumul:
                    status = s
                    break

            est_name = ESTIMATE_NAMES[est_idx % len(ESTIMATE_NAMES)]
            version = 1
            parent_id = None

            # For 2nd and 4th estimates, make them v2 of previous
            if est_idx in (1, 3) and all_estimates:
                prev_candidates = [e for e in all_estimates if e.project_id == pid]
                if prev_candidates:
                    parent = prev_candidates[-1]
                    parent_id = parent.id
                    version = parent.version + 1
                    parent.status = EstimateStatus.SUPERSEDED
                    db.flush()

            tax_rate = random.choice([7.0, 7.25, 7.5, 8.0, 8.25, 8.5, 9.0])

            estimate = Estimate(
                company_id=COMPANY_ID,
                project_id=pid,
                sequence_name=f"EST{est_seq:05d}",
                name=f"{est_name} v{version}",
                description=f"Detailed estimate for project {pid}, version {version}",
                version=version,
                status=status,
                estimate_type=random.choice(["preliminary", "schematic", "detailed"]),
                tax_rate=tax_rate,
                parent_estimate_id=parent_id,
                created_by=USER_ID,
                approved_by=USER_ID if status == EstimateStatus.APPROVED else None,
                approved_date=date(2026, random.randint(1, 3), random.randint(1, 28)) if status == EstimateStatus.APPROVED else None,
            )
            db.add(estimate)
            db.flush()
            est_seq += 1
            all_estimates.append(estimate)
            estimate_count += 1

            # Groups: 3-5 per estimate
            n_groups = random.randint(3, 5)
            groups_for_est = random.sample(ESTIMATE_GROUPS, n_groups)
            est_subtotal = 0.0

            for g_idx, g_name in enumerate(groups_for_est):
                group = EstimateGroup(
                    estimate_id=estimate.id,
                    company_id=COMPANY_ID,
                    name=g_name,
                    display_order=g_idx + 1,
                )
                db.add(group)
                db.flush()
                group_count += 1

                # Line items: 5-10 per group
                n_lines = random.randint(5, 10)
                sample_items = random.sample(all_cost_items, min(n_lines, len(all_cost_items)))
                group_subtotal = 0.0

                for li_idx, ci in enumerate(sample_items):
                    qty = round(random.uniform(5, 500), 1)
                    markup_pct = random.uniform(10, 25)
                    unit_cost = ci.unit_cost
                    unit_price = round(unit_cost * (1 + markup_pct / 100), 2)
                    total_cost = round(qty * unit_cost, 2)
                    total_price = round(qty * unit_price, 2)

                    li = EstimateLineItem(
                        group_id=group.id,
                        estimate_id=estimate.id,
                        company_id=COMPANY_ID,
                        cost_item_id=ci.id,
                        name=ci.name,
                        item_type=line_item_type_map.get(ci.item_type.value, LineItemType.MATERIAL),
                        quantity=qty,
                        unit=ci.unit,
                        unit_cost=unit_cost,
                        unit_price=unit_price,
                        total_cost=total_cost,
                        total_price=total_price,
                        markup_pct=round(markup_pct, 1),
                        taxable=ci.taxable,
                        cost_code=ci.cost_code,
                        display_order=li_idx + 1,
                    )
                    db.add(li)
                    all_line_items.append(li)
                    line_item_count += 1
                    group_subtotal += total_cost
                    est_subtotal += total_cost

                group.subtotal = round(group_subtotal, 2)
                db.flush()

            estimate.subtotal = round(est_subtotal, 2)
            db.flush()

        print(f"  Project {pid}: 5 estimates")

    counts["estimates"] = estimate_count
    counts["estimate_groups"] = group_count
    counts["estimate_line_items"] = line_item_count

    # ==================================================================
    # ESTIMATE MARKUPS (2-3 per estimate)
    # ==================================================================
    print("\n--- Estimate Markups ---")

    markup_count = 0

    for est in all_estimates:
        overhead_pct = round(random.uniform(8, 12), 1)
        profit_pct = round(random.uniform(10, 20), 1)

        overhead_amt = round(est.subtotal * overhead_pct / 100, 2)
        profit_amt = round((est.subtotal + overhead_amt) * profit_pct / 100, 2)

        m1 = EstimateMarkup(
            estimate_id=est.id,
            company_id=COMPANY_ID,
            name="Overhead",
            markup_type=MarkupType.PERCENTAGE,
            value=overhead_pct,
            apply_before_tax=True,
            is_compounding=False,
            display_order=1,
            calculated_amount=overhead_amt,
        )
        m2 = EstimateMarkup(
            estimate_id=est.id,
            company_id=COMPANY_ID,
            name="Profit",
            markup_type=MarkupType.PERCENTAGE,
            value=profit_pct,
            apply_before_tax=True,
            is_compounding=True,
            display_order=2,
            calculated_amount=profit_amt,
        )
        db.add_all([m1, m2])
        markup_count += 2

        # 40% chance of contingency
        if random.random() < 0.4:
            cont_pct = round(random.uniform(3, 5), 1)
            cont_amt = round(est.subtotal * cont_pct / 100, 2)
            m3 = EstimateMarkup(
                estimate_id=est.id,
                company_id=COMPANY_ID,
                name="Contingency",
                markup_type=MarkupType.PERCENTAGE,
                value=cont_pct,
                apply_before_tax=True,
                is_compounding=False,
                display_order=3,
                calculated_amount=cont_amt,
            )
            db.add(m3)
            markup_count += 1

        # Update estimate totals
        total_markup = overhead_amt + profit_amt
        est.markup_total = round(total_markup, 2)
        est.tax_total = round((est.subtotal + total_markup) * est.tax_rate / 100, 2)
        est.grand_total = round(est.subtotal + est.markup_total + est.tax_total, 2)

    db.flush()
    print(f"  {markup_count} markups created")
    counts["estimate_markups"] = markup_count

    # ==================================================================
    # PROPOSALS (1 per approved estimate)
    # ==================================================================
    print("\n--- Proposals ---")

    approved_estimates = [e for e in all_estimates if e.status == EstimateStatus.APPROVED]
    proposal_count = 0
    prop_seq = 1

    proposal_statuses = [ProposalStatus.DRAFT, ProposalStatus.SENT, ProposalStatus.VIEWED, ProposalStatus.APPROVED]
    proposal_status_weights = [0.15, 0.25, 0.25, 0.35]

    for est in approved_estimates:
        r = random.random()
        cumul = 0
        p_status = ProposalStatus.DRAFT
        for s, w in zip(proposal_statuses, proposal_status_weights):
            cumul += w
            if r <= cumul:
                p_status = s
                break

        client = random.choice(CLIENT_NAMES)
        valid_days = random.randint(30, 90)
        base_date = date(2026, random.randint(1, 3), random.randint(1, 28))

        proposal = Proposal(
            company_id=COMPANY_ID,
            sequence_name=f"PROP{prop_seq:05d}",
            estimate_id=est.id,
            project_id=est.project_id,
            name=f"Proposal for {est.name}",
            description=f"Client proposal based on {est.name}",
            status=p_status,
            client_name=client,
            client_email=f"contact@{client.lower().replace(' ', '').replace('.', '').replace(',', '')[:15]}.com",
            client_phone=f"555-{random.randint(1000, 9999)}",
            scope_of_work=f"Complete scope of work as outlined in {est.name} including all materials, labor, and equipment.",
            terms_and_conditions="Net 30 payment terms. Progress billing monthly. 10% retainage until substantial completion.",
            exclusions="Excludes: hazardous material abatement, unforeseen subsurface conditions, permit fees.",
            payment_schedule="30% mobilization, 30% at 50% complete, 30% at substantial completion, 10% at final.",
            valid_until=base_date + timedelta(days=valid_days),
            sent_date=base_date if p_status in (ProposalStatus.SENT, ProposalStatus.VIEWED, ProposalStatus.APPROVED) else None,
            viewed_date=datetime(base_date.year, base_date.month, min(base_date.day + random.randint(1, 5), 28), 14, 30) if p_status in (ProposalStatus.VIEWED, ProposalStatus.APPROVED) else None,
            approved_date=base_date + timedelta(days=random.randint(7, 21)) if p_status == ProposalStatus.APPROVED else None,
            show_line_items=random.choice([True, True, True, False]),
            show_unit_prices=random.choice([True, False, False]),
            show_markup=random.choice([True, False, False, False]),
            show_groups=True,
            version=1,
            created_by=USER_ID,
        )
        db.add(proposal)
        proposal_count += 1
        prop_seq += 1

    db.flush()
    print(f"  {proposal_count} proposals created")
    counts["proposals"] = proposal_count

    # ==================================================================
    # TAKEOFF SHEETS (2-3 per project, with measurements)
    # ==================================================================
    print("\n--- Takeoff Sheets ---")

    sheet_count = 0
    measurement_count = 0
    tk_seq = 1

    mtype_choices = [MeasurementType.LINEAR, MeasurementType.AREA, MeasurementType.COUNT]
    colors = ["#1890ff", "#52c41a", "#f5222d", "#fa8c16", "#722ed1", "#13c2c2", "#eb2f96"]

    for pid in PROJECT_IDS:
        n_sheets = random.randint(2, 3)
        sheet_names = random.sample(TAKEOFF_SHEET_NAMES, n_sheets)

        for s_name in sheet_names:
            sheet = TakeoffSheet(
                company_id=COMPANY_ID,
                project_id=pid,
                sequence_name=f"TK{tk_seq:05d}",
                name=s_name,
                description=f"Takeoff sheet for {s_name}",
                file_name=f"{s_name.lower().replace(' ', '_')}.pdf",
                page_number=random.randint(1, 5),
                scale_factor=random.choice([0.125, 0.25, 0.5, 1.0]),
                scale_unit="ft",
                revision=1,
                created_by=USER_ID,
            )
            db.add(sheet)
            db.flush()
            sheet_count += 1
            tk_seq += 1

            # 3-5 measurements per sheet
            n_meas = random.randint(3, 5)
            labels = random.sample(MEASUREMENT_LABELS, n_meas)

            # Get line items for this project to link some measurements
            project_lines = [li for li in all_line_items if li.estimate_id in
                             [e.id for e in all_estimates if e.project_id == pid]]

            for label in labels:
                mtype = random.choice(mtype_choices)

                if mtype == MeasurementType.LINEAR:
                    value = round(random.uniform(10, 500), 1)
                    unit = "lf"
                elif mtype == MeasurementType.AREA:
                    value = round(random.uniform(100, 10000), 1)
                    unit = "sf"
                else:
                    value = float(random.randint(1, 50))
                    unit = "ea"

                # 50% chance of linking to a line item
                linked_li_id = None
                if project_lines and random.random() < 0.5:
                    linked_li_id = random.choice(project_lines).id

                m = TakeoffMeasurement(
                    sheet_id=sheet.id,
                    company_id=COMPANY_ID,
                    estimate_line_item_id=linked_li_id,
                    measurement_type=mtype,
                    label=label,
                    value=value,
                    unit=unit,
                    color=random.choice(colors),
                    layer=random.choice(["Foundation", "Walls", "Floor", "Roof", "Site", "MEP"]),
                )
                db.add(m)
                measurement_count += 1

        db.flush()

    print(f"  {sheet_count} sheets, {measurement_count} measurements")
    counts["takeoff_sheets"] = sheet_count
    counts["takeoff_measurements"] = measurement_count

    # ==================================================================
    # COMMIT
    # ==================================================================
    db.commit()

    # ==================================================================
    # SUMMARY
    # ==================================================================
    print("\n" + "=" * 60)
    print("SEED COMPLETE — Summary")
    print("=" * 60)
    for table, count in counts.items():
        print(f"  {table:30s} {count:>6d}")
    total = sum(counts.values())
    print(f"  {'TOTAL':30s} {total:>6d}")
    print("=" * 60)


if __name__ == "__main__":
    seed()
