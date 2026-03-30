"""
Seed demo data for ALL 7 AGCM addon modules — realistic construction data.
Run: cd /opt/FastVue/backend && source .venv/bin/activate && ENV_FILE=.env.agcm python -m scripts.seed_all_modules

Assumes:
  - COMPANY_ID=1 and USER_ID=1 already exist
  - Projects with IDs 1-10 already exist (created by agcm seed_demo_data.py)
  - All agcm_* tables already exist (auto-created by AutoSchemaManager)
"""

import os
import sys
import random
import importlib.util
from datetime import date, datetime, timedelta

# ---------------------------------------------------------------------------
# Path setup — same pattern as existing agcm seed script
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
PROJECT_IDS = list(range(1, 11))  # projects 1-10 from existing seed

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

# ---------------------------------------------------------------------------
# Base directory for addon modules
# ---------------------------------------------------------------------------
ADDONS_DIR = os.path.join(os.path.dirname(__file__), '..')

def model_path(module, filename):
    return os.path.abspath(os.path.join(ADDONS_DIR, module, 'models', filename))

# ---------------------------------------------------------------------------
# Realistic data lists
# ---------------------------------------------------------------------------

FOLDER_NAMES = [
    "Drawings", "Specifications", "Contracts", "Permits", "Submittals",
    "RFIs", "Change Orders", "Invoices", "Safety Reports", "Inspection Reports",
    "Photos", "Correspondence", "Meeting Minutes", "Schedules", "Closeout",
]

SUBFOLDER_NAMES = [
    "Architectural", "Structural", "Mechanical", "Electrical", "Plumbing",
    "Civil", "Landscape", "Interior", "Rev A", "Rev B",
]

DOCUMENT_NAMES = [
    "Foundation Plan Rev A", "Structural Drawings Set 2", "Electrical Layout Floor 1",
    "HVAC Ductwork Plan", "Plumbing Riser Diagram", "Site Grading Plan",
    "Roof Framing Details", "Elevator Shaft Section", "Fire Sprinkler Layout",
    "Concrete Mix Design Report", "Soil Boring Analysis", "Steel Connection Details",
    "Window Schedule", "Door Hardware Spec", "Finish Schedule Floor 2",
    "Lighting Control Plan", "Landscape Irrigation Plan", "Parking Lot Striping Plan",
    "ADA Compliance Report", "Stormwater Management Plan", "Building Envelope Details",
    "Curtain Wall Shop Drawings", "Precast Panel Layout", "Waterproofing Membrane Spec",
    "Acoustic Ceiling Plan", "Kitchen Equipment Layout", "Emergency Egress Plan",
    "Signage Location Plan", "Loading Dock Detail", "Utility Trench Profile",
]

DOCUMENT_DESCRIPTIONS = [
    "Updated per architect's RFI response", "Revised for code compliance",
    "Initial submission for review", "Final approved version", "Superseded by Rev B",
    "Pending owner approval", "Issued for construction", "As-built documentation",
    "Shop drawing resubmission", "Per addendum #3 changes",
]

RFI_SUBJECTS = [
    "Concrete strength specification clarification", "Steel beam connection detail",
    "Waterproofing membrane compatibility", "Electrical panel location conflict",
    "HVAC duct routing through structural beam", "Foundation footing depth discrepancy",
    "Window sill height clarification", "Fire rating requirement for corridor walls",
    "Stairwell handrail mounting detail", "Roof drain location vs structural",
    "ADA ramp slope confirmation", "Elevator pit depth requirement",
    "Exterior cladding attachment detail", "Underground utility crossing conflict",
    "Ceiling height at mechanical room", "Floor drain invert elevation",
    "Expansion joint detail at parking garage", "Emergency generator pad location",
    "Grease trap sizing for kitchen", "Loading dock leveler specification",
    "Acoustic insulation requirement between units", "Smoke detector spacing in corridor",
    "Fire damper location at shaft wall", "Concrete slab thickness at server room",
    "Bollard spacing at storefront", "Transformer pad elevation",
    "Gas line routing through building", "Backflow preventer location",
    "Curb and gutter detail at entrance", "Dumpster enclosure height requirement",
]

RFI_QUESTIONS = [
    "Per drawing S-101 detail 3, the beam connection shows a moment connection but the spec calls for a shear connection. Please clarify which is correct.",
    "The architectural drawings show 8'-0\" ceiling height but the mechanical drawings require 12\" of duct space. Can we lower the ceiling to 7'-6\" or reroute ductwork?",
    "The specification section 07 92 00 calls for a specific membrane product that has been discontinued. Is the substitute product acceptable?",
    "There is a conflict between the electrical panel shown on E-201 and the plumbing riser shown on P-301. Which takes priority?",
    "The soil report recommends deeper footings than shown on the structural drawings. Please confirm the required footing depth.",
    "Drawing A-401 shows a window at this location but the structural drawing shows a shear wall. Please clarify.",
    "The fire code requires a 2-hour rating but the detail shows 1-hour assembly. Please confirm the correct rating.",
    "The handrail detail does not match the ADA requirements for graspability. Please provide a revised detail.",
]

RFI_LABEL_NAMES = [
    ("Structural", "#f5222d"), ("Mechanical", "#fa8c16"), ("Electrical", "#fadb14"),
    ("Plumbing", "#52c41a"), ("Architectural", "#1890ff"), ("Civil", "#722ed1"),
    ("Fire Protection", "#eb2f96"), ("Code Compliance", "#13c2c2"),
    ("Owner Request", "#fa541c"), ("Urgent", "#ff4d4f"),
]

SUBMITTAL_TITLES = [
    "Door Hardware Schedule", "HVAC Equipment Submittals", "Concrete Mix Design",
    "Structural Steel Shop Drawings", "Roofing Material Samples", "Light Fixture Cut Sheets",
    "Plumbing Fixture Spec Sheets", "Fire Sprinkler Shop Drawings", "Elevator Equipment Data",
    "Window and Glazing Samples", "Carpet and Flooring Samples", "Paint Color Selections",
    "Acoustic Ceiling Tile Samples", "Kitchen Equipment Cut Sheets", "Generator Spec Submittal",
    "Switchgear Shop Drawings", "Precast Panel Shop Drawings", "Waterproofing Product Data",
    "Handrail and Guardrail Details", "Signage Shop Drawings", "Parking Control Equipment",
    "Security System Shop Drawings", "Telecommunications Equipment", "AV System Components",
    "Landscape Plant List", "Irrigation System Design", "Site Furnishings Catalog",
    "Concrete Formwork Plan", "Rebar Placement Drawings", "Metal Stud Framing Details",
]

SUBMITTAL_DESCRIPTIONS = [
    "Per specification section requirement", "Resubmission with corrections noted",
    "Initial submission for architect review", "Alternate product for owner consideration",
    "Final approved product data", "Expedited review requested", "Coordinated with MEP trades",
    "Updated per addendum changes", "Color and finish selections", "Performance data included",
]

SUBMITTAL_TYPE_NAMES = [
    "Product Data", "Shop Drawings", "Samples", "Test Reports",
    "Certificates", "Design Data", "Manufacturer Instructions", "Closeout Documents",
]

SUBMITTAL_PACKAGE_NAMES = [
    "Division 03 - Concrete", "Division 04 - Masonry", "Division 05 - Metals",
    "Division 06 - Wood/Plastics", "Division 07 - Thermal/Moisture", "Division 08 - Openings",
    "Division 09 - Finishes", "Division 10 - Specialties", "Division 11 - Equipment",
    "Division 12 - Furnishings", "Division 13 - Special Construction",
    "Division 14 - Conveying", "Division 15 - Mechanical", "Division 16 - Electrical",
    "Division 21 - Fire Suppression", "Division 22 - Plumbing", "Division 23 - HVAC",
    "Division 26 - Electrical", "Division 31 - Earthwork", "Division 32 - Exterior",
]

SUBMITTAL_LABEL_NAMES = [
    ("Critical Path", "#f5222d"), ("Long Lead", "#fa8c16"), ("Owner Furnished", "#fadb14"),
    ("Alternate", "#52c41a"), ("Expedite", "#1890ff"), ("Resubmittal", "#722ed1"),
    ("Deferred", "#8c8c8c"), ("Mock-up Required", "#eb2f96"),
]

CO_TITLES = [
    "Additional electrical outlets for server room", "Upgraded HVAC system for data center",
    "Foundation redesign due to soil conditions", "Added fire sprinkler coverage in attic",
    "Exterior facade material change", "Structural reinforcement for rooftop equipment",
    "Additional parking lot lighting", "Elevator cab finish upgrade",
    "Kitchen exhaust hood modification", "ADA restroom reconfiguration",
    "Emergency generator upgrade", "Waterproofing scope extension",
    "Additional concrete reinforcement", "Window specification change to impact-rated",
    "Roof material upgrade to standing seam", "Added security camera infrastructure",
    "Relocate main electrical room", "Additional floor drains in mechanical room",
    "Fire alarm system upgrade", "Landscaping enhancement per owner request",
    "Added loading dock canopy", "Upgraded lobby flooring to marble",
    "Additional signage and wayfinding", "Retaining wall extension",
    "Underground stormwater detention", "Acoustic treatment for conference rooms",
    "IT room cooling system addition", "Exterior painting scope addition",
    "Gas line rerouting", "Additional fencing and gates",
]

CO_REASONS = [
    "Owner requested upgrade", "Design conflict discovered during construction",
    "Code requirement change", "Unforeseen site condition", "Value engineering opportunity",
    "Architect design revision", "Permit requirement", "Safety improvement",
    "Building department requirement", "Scope clarification",
]

CO_LINE_DESCRIPTIONS = [
    "Electrical conduit and wiring", "Concrete demolition and removal", "New concrete pour",
    "Steel fabrication and erection", "Plumbing rough-in", "HVAC ductwork modification",
    "Drywall framing and finishing", "Paint and wall covering", "Flooring installation",
    "Door and hardware", "Window installation", "Roofing material and labor",
    "Fire sprinkler heads and piping", "Light fixtures and switches", "Excavation and grading",
    "Waterproofing membrane application", "Insulation installation", "Ceiling grid and tile",
    "Handrail fabrication", "Equipment pad construction", "Crane rental",
    "Temporary protection and barriers", "Cleanup and debris removal", "Engineering and design",
    "Permit fees", "Testing and inspection", "General conditions and overhead",
]

CO_UNITS = ["EA", "SF", "LF", "CY", "TON", "HR", "LS", "GAL", "SY", "MO"]

TASK_NAMES = [
    "Site preparation", "Foundation excavation", "Concrete pour - foundation",
    "Structural steel erection", "Floor slab pour", "Masonry walls",
    "Roof framing", "Roofing installation", "Exterior wall framing",
    "Window installation", "Door installation", "Plumbing rough-in",
    "Electrical rough-in", "HVAC duct installation", "Fire sprinkler rough-in",
    "Drywall installation", "Taping and finishing", "Interior painting",
    "Tile installation", "Flooring installation", "Ceiling grid installation",
    "Elevator installation", "Fire alarm wiring", "Plumbing fixtures",
    "Electrical fixtures", "HVAC equipment startup", "Landscaping",
    "Parking lot paving", "Striping and signage", "Final inspection",
    "Punch list completion", "Certificate of occupancy", "Owner training",
    "Project closeout", "Demolition", "Temporary utilities",
    "Dewatering", "Pile driving", "Grade beams", "Retaining wall construction",
    "Waterproofing application", "Insulation installation", "Exterior cladding",
    "Stucco application", "Metal panel installation", "Curtain wall installation",
    "Storefront glazing", "Concrete polishing", "Epoxy flooring",
    "Cabinet installation",
]

WBS_ITEMS = [
    ("1.0", "Pre-Construction"), ("2.0", "Site Work"), ("3.0", "Foundation"),
    ("4.0", "Structural"), ("5.0", "Building Envelope"), ("6.0", "MEP Rough-In"),
    ("7.0", "Interior Finishes"), ("8.0", "MEP Trim-Out"), ("9.0", "Site Finishes"),
    ("10.0", "Closeout"),
]

WBS_SUB_ITEMS = {
    "1.0": [("1.1", "Permits & Approvals"), ("1.2", "Mobilization")],
    "2.0": [("2.1", "Earthwork"), ("2.2", "Utilities"), ("2.3", "Paving")],
    "3.0": [("3.1", "Excavation"), ("3.2", "Footings"), ("3.3", "Foundation Walls")],
    "4.0": [("4.1", "Steel Erection"), ("4.2", "Concrete Decks"), ("4.3", "Masonry")],
    "5.0": [("5.1", "Roofing"), ("5.2", "Exterior Walls"), ("5.3", "Windows & Doors")],
    "6.0": [("6.1", "Plumbing"), ("6.2", "HVAC"), ("6.3", "Electrical"), ("6.4", "Fire Protection")],
    "7.0": [("7.1", "Drywall"), ("7.2", "Flooring"), ("7.3", "Ceilings"), ("7.4", "Paint")],
    "8.0": [("8.1", "Plumbing Fixtures"), ("8.2", "HVAC Startup"), ("8.3", "Lighting")],
    "9.0": [("9.1", "Landscaping"), ("9.2", "Signage"), ("9.3", "Final Grading")],
    "10.0": [("10.1", "Punch List"), ("10.2", "Final Inspection"), ("10.3", "Turnover")],
}

COST_CODE_CATEGORIES = [
    ("01", "General Requirements", [
        ("01 10", "Summary of Work"), ("01 30", "Administrative Requirements"),
        ("01 50", "Temporary Facilities"), ("01 70", "Execution and Closeout"),
        ("01 80", "Performance Requirements"), ("01 90", "Life Cycle Activities"),
    ]),
    ("03", "Concrete", [
        ("03 10", "Concrete Forming"), ("03 20", "Concrete Reinforcing"),
        ("03 30", "Cast-in-Place Concrete"), ("03 40", "Precast Concrete"),
    ]),
    ("05", "Metals", [
        ("05 10", "Structural Metal Framing"), ("05 20", "Metal Joists"),
        ("05 30", "Metal Decking"), ("05 50", "Metal Fabrications"),
    ]),
    ("07", "Thermal and Moisture", [
        ("07 10", "Dampproofing"), ("07 20", "Thermal Insulation"),
        ("07 40", "Roofing and Siding"), ("07 90", "Joint Sealants"),
    ]),
    ("09", "Finishes", [
        ("09 20", "Plaster and Gypsum"), ("09 30", "Tiling"),
        ("09 60", "Flooring"), ("09 90", "Painting and Coating"),
    ]),
    ("15", "Mechanical", [
        ("15 10", "Plumbing"), ("15 30", "Fire Protection"),
        ("15 50", "HVAC"), ("15 80", "HVAC Instrumentation"),
    ]),
    ("16", "Electrical", [
        ("16 10", "Electrical General"), ("16 20", "Electrical Power"),
        ("16 40", "Electrical Lighting"), ("16 70", "Communications"),
    ]),
]

BUDGET_DESCRIPTIONS = [
    "Foundation concrete and rebar", "Structural steel supply and erection",
    "Plumbing rough-in labor and materials", "HVAC equipment and ductwork",
    "Electrical distribution and wiring", "Roofing materials and installation",
    "Drywall and framing labor", "Paint and wall finishes", "Flooring and tile",
    "Elevator equipment and installation", "Fire sprinkler system", "Landscape and irrigation",
    "Parking lot paving and striping", "Window and door installation",
    "Temporary facilities and utilities", "General conditions and insurance",
    "Permits and fees", "Testing and inspections", "Cleanup and waste removal",
    "Sitework and grading",
]

EXPENSE_DESCRIPTIONS = [
    "Material delivery - rebar", "Equipment rental - crane", "Equipment rental - excavator",
    "Concrete pump rental", "Scaffolding rental", "Temporary power setup",
    "Dumpster and waste removal", "Portable toilet rental", "Survey and layout services",
    "Material delivery - lumber", "Tool purchase - power tools", "Safety equipment purchase",
    "Fuel for equipment", "Water truck rental", "Generator rental",
    "Material delivery - drywall", "Material delivery - paint", "Concrete testing services",
    "Soil compaction testing", "Welding inspection services",
]

EXPENSE_LINE_ITEMS = [
    ("Rebar #4 grade 60", "TON"), ("Rebar #5 grade 60", "TON"),
    ("Ready-mix concrete 4000 PSI", "CY"), ("Structural steel W-flange", "TON"),
    ("Plywood sheathing 3/4\"", "SF"), ("2x4 studs", "EA"),
    ("Type X drywall 5/8\"", "SF"), ("Joint compound 5-gal", "EA"),
    ("Interior latex paint", "GAL"), ("Ceramic floor tile", "SF"),
    ("Carpet tiles", "SF"), ("Acoustic ceiling tiles", "SF"),
    ("Copper pipe 3/4\"", "LF"), ("PVC pipe 4\"", "LF"),
    ("Electrical wire 12 AWG", "LF"), ("EMT conduit 3/4\"", "LF"),
    ("Fire sprinkler heads", "EA"), ("Insulation R-19", "SF"),
    ("Roofing membrane", "SF"), ("Flashing material", "LF"),
]

VENDOR_NAMES = [
    "ABC Building Supply", "Texas Steel Co.", "Lone Star Concrete",
    "Gulf Coast Plumbing Supply", "Southwest Electrical", "Metro HVAC Solutions",
    "Premier Roofing Materials", "Capitol Glass & Mirror", "Rio Grande Lumber",
    "Bayou Equipment Rentals", "Alamo Fire Protection Supply", "Hill Country Masonry",
    "Dallas Door & Hardware", "Houston Flooring Distributors", "Austin Paint Center",
    "San Antonio Safety Supply", "Corpus Christi Crane Service", "El Paso Aggregates",
    "Fort Worth Fencing", "Galveston Marine Supply",
]

CLIENT_NAMES = [
    "City of Houston", "Memorial Hermann Health", "Texas A&M University",
    "ExxonMobil Corporation", "H-E-B Grocery Company", "Methodist Hospital",
    "HISD School District", "Harris County", "Port of Houston Authority",
    "Texas Children's Hospital", "Baylor College of Medicine", "Rice University",
    "Shell Oil Company", "Chevron Phillips", "NRG Energy",
]

ISSUE_TITLES = [
    "Concrete crack in parking structure", "Water infiltration at joint",
    "HVAC noise exceeds specification", "Elevator door alignment issue",
    "Fire sprinkler head damaged during framing", "Exterior paint peeling",
    "Roof leak at penetration", "Floor tile popping at lobby entrance",
    "Electrical panel overheating", "Plumbing leak in ceiling space",
    "Door closer not latching properly", "Window seal failure with condensation",
    "Drywall crack at corner bead", "Ceiling tile sagging from humidity",
    "Parking lot pothole forming", "Handrail loose at top landing",
    "Emergency light not functioning", "Grout cracking in restroom tile",
    "Retaining wall leaning", "Stormwater drain clogged",
    "Expansion joint missing cover plate", "Elevator cab finish scratched",
    "Loading dock seal damaged", "Exterior signage mounting loose",
    "Concrete spalling at column base", "Cabinet door misaligned",
    "Carpet seam visible in hallway", "Acoustic ceiling damaged by trade",
    "Gas line pressure test failure", "Backflow preventer leaking",
]

ISSUE_DESCRIPTIONS = [
    "Observed during routine inspection. Requires immediate attention.",
    "Reported by subcontractor foreman during walkthrough.",
    "Discovered during commissioning process. Affecting occupancy timeline.",
    "Found during quality control check. Needs repair before covering.",
    "Identified by building inspector. Must resolve before final inspection.",
    "Owner reported during walkthrough. Priority item for punch list.",
]

ISSUE_LOCATIONS = [
    "Floor 1 - Lobby", "Floor 1 - Corridor A", "Floor 2 - Office Wing",
    "Floor 3 - Conference Room", "Basement - Mechanical Room", "Roof - North Section",
    "Exterior - East Facade", "Exterior - South Entry", "Parking Garage - Level 1",
    "Parking Garage - Level 2", "Loading Dock", "Elevator Shaft",
    "Stairwell A", "Stairwell B", "Restroom - Floor 1",
    "Restroom - Floor 2", "Kitchen Area", "Server Room",
    "Electrical Room", "Generator Pad",
]

MILESTONE_NAMES = [
    "Foundation Complete", "Steel Erection Complete", "Roof Dry-In",
    "Building Enclosed", "MEP Rough-In Complete", "Drywall Complete",
    "Interior Finishes Complete", "MEP Trim-Out Complete", "Elevator Inspection",
    "Fire Alarm Acceptance", "HVAC Commissioning Complete", "Substantial Completion",
    "Final Inspection", "Certificate of Occupancy", "Owner Move-In",
    "Punch List Complete", "Final Payment", "Warranty Start",
    "Site Work Complete", "Parking Lot Complete", "Landscaping Complete",
    "Temporary CO Issued", "Structural Inspection", "Plumbing Final",
    "Electrical Final", "Mechanical Final", "ADA Compliance Review",
    "Environmental Clearance", "As-Built Drawings Submitted", "O&M Manuals Delivered",
]

ESTIMATION_GROUPS = [
    "General Conditions", "Site Work", "Concrete", "Masonry", "Metals",
    "Wood and Plastics", "Thermal Protection", "Doors and Windows",
    "Finishes", "Specialties", "Equipment", "Furnishings",
    "Special Construction", "Conveying Systems", "Mechanical", "Electrical",
]

ESTIMATION_ITEMS = [
    ("Mobilization and setup", "fee", "LS"),
    ("Site clearing", "subcontractor", "AC"),
    ("Excavation", "subcontractor", "CY"),
    ("Concrete footings", "material", "CY"),
    ("Rebar supply", "material", "TON"),
    ("Concrete labor", "labor", "HR"),
    ("Structural steel supply", "material", "TON"),
    ("Steel erection labor", "labor", "HR"),
    ("Crane rental", "equipment", "DAY"),
    ("Masonry block", "material", "SF"),
    ("Mason labor", "labor", "HR"),
    ("Roofing membrane", "material", "SF"),
    ("Roofing labor", "subcontractor", "SF"),
    ("Drywall supply", "material", "SF"),
    ("Drywall labor", "labor", "SF"),
    ("Paint supply", "material", "GAL"),
    ("Paint labor", "labor", "SF"),
    ("Floor tile supply", "material", "SF"),
    ("Tile labor", "labor", "SF"),
    ("Plumbing rough-in", "subcontractor", "LS"),
    ("HVAC equipment", "equipment", "LS"),
    ("Electrical wiring", "subcontractor", "LS"),
    ("Fire sprinkler system", "subcontractor", "LS"),
    ("Elevator installation", "subcontractor", "LS"),
    ("Contingency allowance", "allowance", "LS"),
]

IMAGE_NAMES = [
    "Foundation excavation progress", "Concrete pour in progress",
    "Steel erection - floor 2", "Roofing installation", "Exterior wall framing",
    "Window installation north side", "Interior framing corridor",
    "MEP rough-in overhead", "Drywall installation floor 1", "Tile work restroom",
    "Paint preparation lobby", "Ceiling grid installation", "Parking lot paving",
    "Landscaping planting", "Final inspection walkthrough",
    "Aerial site photo", "Equipment on site", "Material staging area",
    "Safety meeting", "Quality control check",
]

IMAGE_TAGS_LIST = [
    "foundation,concrete,excavation", "concrete,pour,progress",
    "steel,erection,structural", "roofing,membrane,installation",
    "framing,exterior,sheathing", "windows,glazing,installation",
    "framing,interior,corridor", "MEP,plumbing,electrical",
    "drywall,interior,finish", "tile,restroom,finish",
    "paint,lobby,preparation", "ceiling,grid,acoustic",
    "paving,asphalt,parking", "landscape,planting,irrigation",
    "inspection,walkthrough,final", "aerial,drone,site",
    "equipment,crane,delivery", "materials,staging,laydown",
    "safety,meeting,training", "QC,inspection,quality",
]


# ============================================================================
# SEED FUNCTION
# ============================================================================

def seed():
    random.seed(42)  # reproducible

    print("=" * 60)
    print("SEEDING ALL 7 AGCM ADDON MODULES")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Load all model files via importlib.util
    # ------------------------------------------------------------------
    print("\nLoading model files...")

    # Load base models first (Company, User, Project referenced by relationships)
    base_agcm_models = [
        'lookups', 'project', 'daily_activity_log', 'manpower', 'weather',
        'notes', 'inspection', 'accident', 'visitor', 'safety_violation',
        'delay', 'deficiency', 'photo',
    ]
    for mf in base_agcm_models:
        load_model(f'_agcm_base_{mf}', model_path('agcm', f'{mf}.py'))

    # Also ensure core app models are loaded
    try:
        from app.models import User, Company  # noqa: F401
    except Exception:
        pass

    # Module 1: agcm_document
    mod_folder = load_model('_agcm_doc_folder', model_path('agcm_document', 'folder.py'))
    mod_document = load_model('_agcm_doc_document', model_path('agcm_document', 'document.py'))

    # Module 2: agcm_rfi
    mod_rfi = load_model('_agcm_rfi', model_path('agcm_rfi', 'rfi.py'))
    mod_rfi_response = load_model('_agcm_rfi_response', model_path('agcm_rfi', 'rfi_response.py'))

    # Module 3: agcm_submittal
    mod_submittal = load_model('_agcm_submittal', model_path('agcm_submittal', 'submittal.py'))

    # Module 4: agcm_change_order
    mod_co = load_model('_agcm_change_order', model_path('agcm_change_order', 'change_order.py'))

    # Module 5: agcm_schedule
    mod_schedule = load_model('_agcm_schedule', model_path('agcm_schedule', 'schedule.py'))
    mod_wbs = load_model('_agcm_wbs', model_path('agcm_schedule', 'wbs.py'))
    mod_task = load_model('_agcm_task', model_path('agcm_schedule', 'task.py'))
    mod_dependency = load_model('_agcm_dependency', model_path('agcm_schedule', 'dependency.py'))

    # Module 6: agcm_finance
    mod_cost_code = load_model('_agcm_cost_code', model_path('agcm_finance', 'cost_code.py'))
    mod_budget = load_model('_agcm_budget', model_path('agcm_finance', 'budget.py'))
    mod_expense = load_model('_agcm_expense', model_path('agcm_finance', 'expense.py'))
    mod_invoice = load_model('_agcm_invoice', model_path('agcm_finance', 'invoice.py'))
    mod_bill = load_model('_agcm_bill', model_path('agcm_finance', 'bill.py'))

    # Module 7: agcm_progress
    mod_milestone = load_model('_agcm_milestone', model_path('agcm_progress', 'milestone.py'))
    mod_issue = load_model('_agcm_issue', model_path('agcm_progress', 'issue.py'))
    mod_estimation = load_model('_agcm_estimation', model_path('agcm_progress', 'estimation.py'))
    mod_scurve = load_model('_agcm_scurve', model_path('agcm_progress', 'scurve.py'))
    mod_image = load_model('_agcm_image', model_path('agcm_progress', 'project_image.py'))

    # Extract classes
    ProjectFolder = mod_folder.ProjectFolder
    ProjectDocument = mod_document.ProjectDocument
    DocumentType = mod_document.DocumentType
    DocumentStatus = mod_document.DocumentStatus

    RFI = mod_rfi.RFI
    RFILabel = mod_rfi.RFILabel
    agcm_rfi_label_rel = mod_rfi.agcm_rfi_label_rel
    agcm_rfi_assignees = mod_rfi.agcm_rfi_assignees
    RFIResponse = mod_rfi_response.RFIResponse

    Submittal = mod_submittal.Submittal
    SubmittalPackage = mod_submittal.SubmittalPackage
    SubmittalType = mod_submittal.SubmittalType
    SubmittalLabel = mod_submittal.SubmittalLabel
    SubmittalApprover = mod_submittal.SubmittalApprover
    agcm_submittal_label_rel = mod_submittal.agcm_submittal_label_rel

    ChangeOrder = mod_co.ChangeOrder
    ChangeOrderLine = mod_co.ChangeOrderLine

    Schedule = mod_schedule.Schedule
    WBS = mod_wbs.WBS
    Task = mod_task.Task
    TaskDependency = mod_dependency.TaskDependency

    CostCode = mod_cost_code.CostCode
    Budget = mod_budget.Budget
    Expense = mod_expense.Expense
    ExpenseLine = mod_expense.ExpenseLine
    Invoice = mod_invoice.Invoice
    Bill = mod_bill.Bill

    Milestone = mod_milestone.Milestone
    Issue = mod_issue.Issue
    EstimationItem = mod_estimation.EstimationItem
    SCurveData = mod_scurve.SCurveData
    ProjectImage = mod_image.ProjectImage

    # Counters for summary
    counts = {}

    # ==================================================================
    # MODULE 1: DOCUMENT MANAGEMENT
    # ==================================================================
    print("\n--- Module 1: Document Management ---")

    # Folders: 60 (6 per project, some nested)
    print("  Folders...")
    folder_ids = {}  # {project_id: [folder_id, ...]}
    folder_count = 0
    for pid in PROJECT_IDS:
        folder_ids[pid] = []
        parent_folders = random.sample(FOLDER_NAMES, 6)
        for fname in parent_folders:
            folder_count += 1
            f = ProjectFolder(
                name=fname,
                parent_id=None,
                project_id=pid,
                company_id=COMPANY_ID,
            )
            db.add(f)
            db.flush()
            folder_ids[pid].append(f.id)
            # 50% chance of a subfolder
            if random.random() < 0.5:
                folder_count += 1
                sf = ProjectFolder(
                    name=random.choice(SUBFOLDER_NAMES),
                    parent_id=f.id,
                    project_id=pid,
                    company_id=COMPANY_ID,
                )
                db.add(sf)
                db.flush()
                folder_ids[pid].append(sf.id)
    db.commit()
    counts['ProjectFolder'] = folder_count
    print(f"    Created {folder_count} folders")

    # Documents: 100+
    print("  Documents...")
    doc_count = 0
    doc_types = list(DocumentType)
    doc_statuses = list(DocumentStatus)
    for pid in PROJECT_IDS:
        for i in range(random.randint(10, 14)):
            doc_count += 1
            doc_name = random.choice(DOCUMENT_NAMES)
            dtype = random.choice(doc_types)
            dstatus = random.choice(doc_statuses)
            d = ProjectDocument(
                company_id=COMPANY_ID,
                sequence_name=f"DOC{doc_count:05d}",
                name=doc_name,
                description=random.choice(DOCUMENT_DESCRIPTIONS),
                document_type=dtype,
                status=dstatus,
                revision=random.randint(1, 5),
                file_name=f"{doc_name.lower().replace(' ', '_')}.pdf",
                file_url=f"/uploads/agcm/documents/{pid}/{doc_name.lower().replace(' ', '_')}.pdf",
                folder_id=random.choice(folder_ids[pid]) if folder_ids[pid] else None,
                project_id=pid,
                uploaded_by=USER_ID,
            )
            db.add(d)
        if pid % 3 == 0:
            db.commit()
    db.commit()
    counts['ProjectDocument'] = doc_count
    print(f"    Created {doc_count} documents")

    # ==================================================================
    # MODULE 2: RFI
    # ==================================================================
    print("\n--- Module 2: RFI ---")

    # RFI Labels: 10
    print("  RFI Labels...")
    rfi_label_ids = []
    for name, color in RFI_LABEL_NAMES:
        lbl = RFILabel(name=name, color=color, company_id=COMPANY_ID)
        db.add(lbl)
        db.flush()
        rfi_label_ids.append(lbl.id)
    db.commit()
    counts['RFILabel'] = len(rfi_label_ids)

    # RFIs: 60+
    print("  RFIs...")
    rfi_ids = []
    rfi_count = 0
    rfi_statuses = ["draft", "open", "in_progress", "answered", "closed"]
    rfi_priorities = ["low", "medium", "high"]
    for pid in PROJECT_IDS:
        for i in range(random.randint(6, 8)):
            rfi_count += 1
            status = random.choice(rfi_statuses)
            base_date = date(2025, 6, 1) + timedelta(days=random.randint(0, 180))
            closed_dt = base_date + timedelta(days=random.randint(3, 30)) if status == "closed" else None
            rfi = RFI(
                company_id=COMPANY_ID,
                sequence_name=f"RFI{rfi_count:05d}",
                subject=random.choice(RFI_SUBJECTS),
                question=random.choice(RFI_QUESTIONS),
                priority=random.choice(rfi_priorities),
                status=status,
                schedule_impact_days=random.choice([0, 0, 0, 1, 2, 3, 5, 7, 14]),
                cost_impact=round(random.choice([0, 0, 0, 500, 1500, 5000, 15000, 50000]), 2),
                due_date=base_date + timedelta(days=14),
                closed_date=closed_dt,
                project_id=pid,
                created_by_user_id=USER_ID,
            )
            db.add(rfi)
            db.flush()
            rfi_ids.append(rfi.id)

            # M2M: labels (1-3 per RFI)
            chosen_labels = random.sample(rfi_label_ids, random.randint(1, 3))
            for lid in chosen_labels:
                db.execute(agcm_rfi_label_rel.insert().values(rfi_id=rfi.id, label_id=lid))

            # M2M: assignees
            db.execute(agcm_rfi_assignees.insert().values(rfi_id=rfi.id, user_id=USER_ID))

    db.commit()
    counts['RFI'] = rfi_count
    print(f"    Created {rfi_count} RFIs")

    # RFI Responses: 120+ (2 per RFI)
    print("  RFI Responses...")
    resp_count = 0
    for rfi_id in rfi_ids:
        for r in range(random.randint(1, 3)):
            resp_count += 1
            is_official = (r == 0 and random.random() < 0.4)
            resp = RFIResponse(
                company_id=COMPANY_ID,
                rfi_id=rfi_id,
                parent_id=None,
                content=random.choice([
                    "Please refer to drawing detail A-301/5 for clarification on this item.",
                    "We will issue a revised drawing by end of week to address this concern.",
                    "The specification takes precedence over the drawing. Proceed per spec section.",
                    "This requires a formal change order. Please submit CO request.",
                    "Confirmed with structural engineer. Proceed as shown on drawing.",
                    "Additional investigation required. Site visit scheduled for Tuesday.",
                    "Owner has approved the alternate approach. Please document in submittal.",
                    "The general contractor shall coordinate with MEP trades to resolve.",
                    "Refer to addendum #2 which supersedes the original drawing detail.",
                    "No schedule impact anticipated. Proceed with work as planned.",
                ]),
                is_official_response=is_official,
                responded_by=USER_ID,
            )
            db.add(resp)
        if resp_count % 50 == 0:
            db.commit()
    db.commit()
    counts['RFIResponse'] = resp_count
    print(f"    Created {resp_count} RFI responses")

    # ==================================================================
    # MODULE 3: SUBMITTALS
    # ==================================================================
    print("\n--- Module 3: Submittals ---")

    # Submittal Types: 8
    print("  Submittal Types...")
    sub_type_ids = []
    for tname in SUBMITTAL_TYPE_NAMES:
        st = SubmittalType(name=tname, company_id=COMPANY_ID)
        db.add(st)
        db.flush()
        sub_type_ids.append(st.id)
    db.commit()
    counts['SubmittalType'] = len(sub_type_ids)

    # Submittal Packages: 20
    print("  Submittal Packages...")
    pkg_ids = {}  # {project_id: [pkg_id, ...]}
    pkg_count = 0
    for pid in PROJECT_IDS:
        pkg_ids[pid] = []
        chosen_pkgs = random.sample(SUBMITTAL_PACKAGE_NAMES, 2)
        for pname in chosen_pkgs:
            pkg_count += 1
            pkg = SubmittalPackage(
                name=pname,
                description=f"Submittal package for {pname.split(' - ')[1] if ' - ' in pname else pname}",
                project_id=pid,
                company_id=COMPANY_ID,
            )
            db.add(pkg)
            db.flush()
            pkg_ids[pid].append(pkg.id)
    db.commit()
    counts['SubmittalPackage'] = pkg_count

    # Submittal Labels: 8
    print("  Submittal Labels...")
    sub_label_ids = []
    for name, color in SUBMITTAL_LABEL_NAMES:
        sl = SubmittalLabel(name=name, color=color, company_id=COMPANY_ID)
        db.add(sl)
        db.flush()
        sub_label_ids.append(sl.id)
    db.commit()
    counts['SubmittalLabel'] = len(sub_label_ids)

    # Submittals: 60+
    print("  Submittals...")
    submittal_ids = []
    sub_count = 0
    sub_statuses = ["draft", "pending_review", "in_review", "approved", "approved_with_comments", "rejected", "resubmitted"]
    sub_priorities = ["low", "medium", "high", "urgent"]
    for pid in PROJECT_IDS:
        for i in range(random.randint(6, 8)):
            sub_count += 1
            base_date = date(2025, 3, 1) + timedelta(days=random.randint(0, 200))
            status = random.choice(sub_statuses)
            sub = Submittal(
                company_id=COMPANY_ID,
                sequence_name=f"SUB{sub_count:05d}",
                title=random.choice(SUBMITTAL_TITLES),
                description=random.choice(SUBMITTAL_DESCRIPTIONS),
                spec_section=f"{random.randint(1, 16):02d} {random.randint(10, 99):02d} 00",
                status=status,
                priority=random.choice(sub_priorities),
                revision=random.randint(1, 3),
                due_date=base_date + timedelta(days=14),
                submitted_date=base_date if status != "draft" else None,
                received_date=base_date + timedelta(days=random.randint(1, 5)) if status not in ("draft", "pending_review") else None,
                package_id=random.choice(pkg_ids[pid]) if pkg_ids[pid] else None,
                type_id=random.choice(sub_type_ids),
                project_id=pid,
                submitted_by=USER_ID,
            )
            db.add(sub)
            db.flush()
            submittal_ids.append(sub.id)

            # M2M: labels (1-2 per submittal)
            chosen_labels = random.sample(sub_label_ids, random.randint(1, 2))
            for lid in chosen_labels:
                db.execute(agcm_submittal_label_rel.insert().values(submittal_id=sub.id, label_id=lid))

    db.commit()
    counts['Submittal'] = sub_count
    print(f"    Created {sub_count} submittals")

    # Submittal Approvers: 120+ (2 per submittal)
    print("  Submittal Approvers...")
    approver_count = 0
    approver_statuses = ["pending", "approved", "approved_as_noted", "rejected", "revise_and_submit"]
    for sid in submittal_ids:
        for seq in range(1, random.randint(2, 4)):
            approver_count += 1
            a_status = random.choice(approver_statuses) if seq == 1 else "pending"
            signed = datetime.now() - timedelta(days=random.randint(1, 60)) if a_status != "pending" else None
            appr = SubmittalApprover(
                submittal_id=sid,
                user_id=USER_ID,
                sequence=seq,
                status=a_status,
                comments=random.choice([
                    None, None,
                    "Approved as submitted", "See redline comments on attachment",
                    "Revise section 3 and resubmit", "Approved with minor corrections noted",
                    "Rejected - does not meet specification requirements",
                ]),
                signed_at=signed,
                company_id=COMPANY_ID,
            )
            db.add(appr)
        if approver_count % 50 == 0:
            db.commit()
    db.commit()
    counts['SubmittalApprover'] = approver_count
    print(f"    Created {approver_count} submittal approvers")

    # ==================================================================
    # MODULE 4: CHANGE ORDERS
    # ==================================================================
    print("\n--- Module 4: Change Orders ---")

    # Change Orders: 60+
    print("  Change Orders...")
    co_ids = []
    co_count = 0
    co_statuses = ["draft", "pending", "approved", "rejected", "void"]
    for pid in PROJECT_IDS:
        for i in range(random.randint(6, 8)):
            co_count += 1
            status = random.choice(co_statuses)
            req_date = date(2025, 4, 1) + timedelta(days=random.randint(0, 200))
            cost = round(random.uniform(2000, 250000), 2)
            co = ChangeOrder(
                company_id=COMPANY_ID,
                sequence_name=f"CO{co_count:05d}",
                title=random.choice(CO_TITLES),
                description=f"Change order for scope modification. {random.choice(CO_REASONS)}.",
                reason=random.choice(CO_REASONS),
                status=status,
                cost_impact=cost if random.random() < 0.8 else -round(random.uniform(1000, 50000), 2),
                schedule_impact_days=random.choice([0, 0, 0, 2, 5, 7, 10, 14, 21, 30]),
                requested_date=req_date,
                approved_date=req_date + timedelta(days=random.randint(5, 30)) if status in ("approved",) else None,
                project_id=pid,
                requested_by=USER_ID,
                approved_by=USER_ID if status == "approved" else None,
            )
            db.add(co)
            db.flush()
            co_ids.append(co.id)
    db.commit()
    counts['ChangeOrder'] = co_count
    print(f"    Created {co_count} change orders")

    # Change Order Lines: 180+ (3 per CO)
    print("  Change Order Lines...")
    col_count = 0
    for co_id in co_ids:
        for _ in range(random.randint(2, 4)):
            col_count += 1
            qty = round(random.uniform(1, 500), 1)
            unit_cost = round(random.uniform(5, 2000), 2)
            total = round(qty * unit_cost, 2)
            line = ChangeOrderLine(
                change_order_id=co_id,
                description=random.choice(CO_LINE_DESCRIPTIONS),
                quantity=qty,
                unit=random.choice(CO_UNITS),
                unit_cost=unit_cost,
                total_cost=total,
                company_id=COMPANY_ID,
            )
            db.add(line)
        if col_count % 100 == 0:
            db.commit()
    db.commit()
    counts['ChangeOrderLine'] = col_count
    print(f"    Created {col_count} change order lines")

    # ==================================================================
    # MODULE 5: SCHEDULE
    # ==================================================================
    print("\n--- Module 5: Schedule ---")

    # Schedules: 10 (1 per project)
    print("  Schedules...")
    schedule_ids = {}  # {project_id: schedule_id}
    for idx, pid in enumerate(PROJECT_IDS):
        sched = Schedule(
            company_id=COMPANY_ID,
            sequence_name=f"SCHED{idx+1:05d}",
            name=f"Master Schedule v1",
            version=1,
            schedule_type=random.choice(["baseline", "revised", "current"]),
            is_active=True,
            project_id=pid,
        )
        db.add(sched)
        db.flush()
        schedule_ids[pid] = sched.id
    db.commit()
    counts['Schedule'] = len(schedule_ids)
    print(f"    Created {len(schedule_ids)} schedules")

    # WBS: 50+ (hierarchical, per project)
    print("  WBS Items...")
    wbs_ids = {}  # {project_id: [wbs_id, ...]}
    wbs_count = 0
    for pid in PROJECT_IDS:
        wbs_ids[pid] = []
        sid = schedule_ids[pid]
        parent_map = {}
        for code, name in WBS_ITEMS:
            wbs_count += 1
            w = WBS(
                code=code, name=name, parent_id=None,
                schedule_id=sid, project_id=pid, company_id=COMPANY_ID,
            )
            db.add(w)
            db.flush()
            wbs_ids[pid].append(w.id)
            parent_map[code] = w.id
            # Sub-items
            if code in WBS_SUB_ITEMS:
                for sub_code, sub_name in WBS_SUB_ITEMS[code]:
                    wbs_count += 1
                    sw = WBS(
                        code=sub_code, name=sub_name, parent_id=parent_map[code],
                        schedule_id=sid, project_id=pid, company_id=COMPANY_ID,
                    )
                    db.add(sw)
                    db.flush()
                    wbs_ids[pid].append(sw.id)
    db.commit()
    counts['WBS'] = wbs_count
    print(f"    Created {wbs_count} WBS items")

    # Tasks: 100+ (10 per project)
    print("  Tasks...")
    task_ids_by_project = {}  # {project_id: [task_id, ...]}
    task_count = 0
    task_statuses = ["todo", "in_progress", "in_review", "completed"]
    task_types = ["task", "milestone"]
    work_types = ["work", "delivery", "inspection", "roadblock", "safety", "downtime"]
    for pid in PROJECT_IDS:
        task_ids_by_project[pid] = []
        sid = schedule_ids[pid]
        wbs_list = wbs_ids[pid]
        base_start = date(2025, 3, 1) + timedelta(days=random.randint(0, 30))
        chosen_tasks = random.sample(TASK_NAMES, min(12, len(TASK_NAMES)))
        for i, tname in enumerate(chosen_tasks):
            task_count += 1
            planned_start = base_start + timedelta(days=i * random.randint(5, 15))
            duration = random.randint(3, 30)
            planned_end = planned_start + timedelta(days=duration)
            progress = random.randint(0, 100)
            status = "completed" if progress == 100 else random.choice(task_statuses[:3])
            is_milestone = (random.random() < 0.15)
            t = Task(
                company_id=COMPANY_ID,
                sequence_name=f"TSK{task_count:05d}",
                name=tname,
                description=f"Task for {tname.lower()} activities",
                task_type="milestone" if is_milestone else "task",
                work_type=random.choice(work_types),
                status=status,
                planned_start=planned_start,
                planned_end=planned_end,
                actual_start=planned_start + timedelta(days=random.randint(-2, 5)) if progress > 0 else None,
                actual_end=planned_end + timedelta(days=random.randint(-3, 7)) if progress == 100 else None,
                duration_days=duration,
                progress=progress,
                total_float=round(random.uniform(-5, 20), 1),
                free_float=round(random.uniform(0, 10), 1),
                is_critical=(random.random() < 0.3),
                wbs_id=random.choice(wbs_list) if wbs_list else None,
                schedule_id=sid,
                assigned_to=USER_ID,
                project_id=pid,
            )
            db.add(t)
            db.flush()
            task_ids_by_project[pid].append(t.id)
    db.commit()
    counts['Task'] = task_count
    print(f"    Created {task_count} tasks")

    # Task Dependencies: 80+ (chain tasks within each project)
    print("  Task Dependencies...")
    dep_count = 0
    dep_types = ["FS", "SS", "FF", "SF"]
    for pid in PROJECT_IDS:
        task_list = task_ids_by_project[pid]
        # Chain sequential tasks as FS dependencies
        for i in range(len(task_list) - 1):
            dep_count += 1
            dep = TaskDependency(
                predecessor_id=task_list[i],
                successor_id=task_list[i + 1],
                dependency_type=random.choices(dep_types, weights=[70, 15, 10, 5])[0],
                lag_days=random.choice([0, 0, 0, 1, 2, 3]),
                company_id=COMPANY_ID,
            )
            db.add(dep)
    db.commit()
    counts['TaskDependency'] = dep_count
    print(f"    Created {dep_count} task dependencies")

    # ==================================================================
    # MODULE 6: FINANCE
    # ==================================================================
    print("\n--- Module 6: Finance ---")

    # Cost Codes: 60+ (hierarchical)
    print("  Cost Codes...")
    cost_code_ids = {}  # {project_id: [cc_id, ...]}
    cc_count = 0
    for pid in PROJECT_IDS:
        cost_code_ids[pid] = []
        for cat_code, cat_name, children in COST_CODE_CATEGORIES:
            cc_count += 1
            parent_cc = CostCode(
                code=cat_code,
                name=cat_name,
                category=cat_name,
                parent_id=None,
                project_id=pid,
                company_id=COMPANY_ID,
            )
            db.add(parent_cc)
            db.flush()
            cost_code_ids[pid].append(parent_cc.id)
            for child_code, child_name in children:
                cc_count += 1
                child_cc = CostCode(
                    code=child_code,
                    name=child_name,
                    category=cat_name,
                    parent_id=parent_cc.id,
                    project_id=pid,
                    company_id=COMPANY_ID,
                )
                db.add(child_cc)
                db.flush()
                cost_code_ids[pid].append(child_cc.id)
        if pid % 3 == 0:
            db.commit()
    db.commit()
    counts['CostCode'] = cc_count
    print(f"    Created {cc_count} cost codes")

    # Budgets: 60+ (6+ per project)
    print("  Budgets...")
    budget_count = 0
    for pid in PROJECT_IDS:
        cc_list = cost_code_ids[pid]
        for i in range(random.randint(6, 8)):
            budget_count += 1
            planned = round(random.uniform(25000, 500000), 2)
            actual = round(planned * random.uniform(0.4, 1.1), 2)
            committed = round(planned * random.uniform(0.6, 1.0), 2)
            b = Budget(
                project_id=pid,
                cost_code_id=random.choice(cc_list) if cc_list else None,
                description=random.choice(BUDGET_DESCRIPTIONS),
                planned_amount=planned,
                actual_amount=actual,
                committed_amount=committed,
                company_id=COMPANY_ID,
            )
            db.add(b)
    db.commit()
    counts['Budget'] = budget_count
    print(f"    Created {budget_count} budgets")

    # Expenses: 60+ with Lines: 180+
    print("  Expenses and Lines...")
    expense_count = 0
    expense_line_count = 0
    exp_statuses = ["draft", "submitted", "approved", "paid"]
    for pid in PROJECT_IDS:
        cc_list = cost_code_ids[pid]
        for i in range(random.randint(6, 8)):
            expense_count += 1
            exp = Expense(
                company_id=COMPANY_ID,
                sequence_name=f"EXP{expense_count:05d}",
                description=random.choice(EXPENSE_DESCRIPTIONS),
                vendor=random.choice(VENDOR_NAMES),
                status=random.choice(exp_statuses),
                project_id=pid,
            )
            db.add(exp)
            db.flush()

            # 2-4 lines per expense
            for _ in range(random.randint(2, 4)):
                expense_line_count += 1
                item_desc, unit = random.choice(EXPENSE_LINE_ITEMS)
                qty = round(random.uniform(1, 200), 1)
                uc = round(random.uniform(5, 500), 2)
                el = ExpenseLine(
                    expense_id=exp.id,
                    description=item_desc,
                    quantity=qty,
                    unit=unit,
                    unit_cost=uc,
                    total_cost=round(qty * uc, 2),
                    cost_code_id=random.choice(cc_list) if cc_list and random.random() < 0.7 else None,
                    category=random.choice(["Material", "Labor", "Equipment", "Subcontractor", "Other"]),
                    company_id=COMPANY_ID,
                )
                db.add(el)
        if pid % 3 == 0:
            db.commit()
    db.commit()
    counts['Expense'] = expense_count
    counts['ExpenseLine'] = expense_line_count
    print(f"    Created {expense_count} expenses, {expense_line_count} expense lines")

    # Invoices: 60+
    print("  Invoices...")
    inv_count = 0
    inv_statuses = ["draft", "sent", "paid", "overdue", "void"]
    for pid in PROJECT_IDS:
        for i in range(random.randint(6, 8)):
            inv_count += 1
            amount = round(random.uniform(10000, 500000), 2)
            tax = round(amount * 0.0825, 2)
            total = round(amount + tax, 2)
            status = random.choice(inv_statuses)
            paid_amt = total if status == "paid" else round(total * random.uniform(0, 0.5), 2) if status in ("sent", "overdue") else 0
            issue_dt = date(2025, 1, 1) + timedelta(days=random.randint(0, 300))
            inv = Invoice(
                company_id=COMPANY_ID,
                sequence_name=f"INV{inv_count:05d}",
                invoice_number=f"INV-{2025}-{inv_count:04d}",
                client_name=random.choice(CLIENT_NAMES),
                status=status,
                amount=amount,
                tax_amount=tax,
                total_amount=total,
                paid_amount=paid_amt,
                balance_due=round(total - paid_amt, 2),
                issue_date=issue_dt,
                due_date=issue_dt + timedelta(days=30),
                paid_date=issue_dt + timedelta(days=random.randint(15, 45)) if status == "paid" else None,
                project_id=pid,
            )
            db.add(inv)
    db.commit()
    counts['Invoice'] = inv_count
    print(f"    Created {inv_count} invoices")

    # Bills: 60+
    print("  Bills...")
    bill_count = 0
    bill_statuses = ["draft", "received", "approved", "paid", "overdue"]
    for pid in PROJECT_IDS:
        for i in range(random.randint(6, 8)):
            bill_count += 1
            amount = round(random.uniform(2000, 150000), 2)
            tax = round(amount * 0.0825, 2)
            total = round(amount + tax, 2)
            status = random.choice(bill_statuses)
            paid_amt = total if status == "paid" else 0
            issue_dt = date(2025, 2, 1) + timedelta(days=random.randint(0, 280))
            bill = Bill(
                company_id=COMPANY_ID,
                sequence_name=f"BILL{bill_count:05d}",
                bill_number=f"BILL-{2025}-{bill_count:04d}",
                vendor_name=random.choice(VENDOR_NAMES),
                status=status,
                amount=amount,
                tax_amount=tax,
                total_amount=total,
                paid_amount=paid_amt,
                issue_date=issue_dt,
                due_date=issue_dt + timedelta(days=30),
                paid_date=issue_dt + timedelta(days=random.randint(10, 40)) if status == "paid" else None,
                project_id=pid,
            )
            db.add(bill)
    db.commit()
    counts['Bill'] = bill_count
    print(f"    Created {bill_count} bills")

    # ==================================================================
    # MODULE 7: PROGRESS
    # ==================================================================
    print("\n--- Module 7: Progress ---")

    # Milestones: 60+
    print("  Milestones...")
    ms_count = 0
    for pid in PROJECT_IDS:
        chosen_milestones = random.sample(MILESTONE_NAMES, random.randint(6, 10))
        for i, mname in enumerate(chosen_milestones):
            ms_count += 1
            planned_dt = date(2025, 3, 1) + timedelta(days=i * random.randint(20, 40))
            is_done = random.random() < 0.35
            ms = Milestone(
                company_id=COMPANY_ID,
                sequence_name=f"MS{ms_count:05d}",
                name=mname,
                description=f"Milestone: {mname} for project #{pid}",
                planned_date=planned_dt,
                actual_date=planned_dt + timedelta(days=random.randint(-5, 10)) if is_done else None,
                is_completed=is_done,
                project_id=pid,
            )
            db.add(ms)
    db.commit()
    counts['Milestone'] = ms_count
    print(f"    Created {ms_count} milestones")

    # Issues: 80+
    print("  Issues...")
    issue_count = 0
    issue_severities = ["critical", "major", "minor", "trivial"]
    issue_statuses = ["open", "in_progress", "resolved", "closed"]
    issue_priorities = ["low", "medium", "high"]
    for pid in PROJECT_IDS:
        for i in range(random.randint(8, 10)):
            issue_count += 1
            status = random.choice(issue_statuses)
            due_dt = date(2025, 6, 1) + timedelta(days=random.randint(0, 200))
            iss = Issue(
                company_id=COMPANY_ID,
                sequence_name=f"ISS{issue_count:05d}",
                title=random.choice(ISSUE_TITLES),
                description=random.choice(ISSUE_DESCRIPTIONS),
                severity=random.choice(issue_severities),
                status=status,
                priority=random.choice(issue_priorities),
                location=random.choice(ISSUE_LOCATIONS),
                due_date=due_dt,
                resolved_date=due_dt + timedelta(days=random.randint(1, 14)) if status in ("resolved", "closed") else None,
                assigned_to=USER_ID,
                reported_by=USER_ID,
                project_id=pid,
            )
            db.add(iss)
    db.commit()
    counts['Issue'] = issue_count
    print(f"    Created {issue_count} issues")

    # Estimation Items: 80+ (hierarchical — groups with children)
    print("  Estimation Items...")
    est_count = 0
    for pid in PROJECT_IDS:
        # Create 2 group parents per project
        for grp_name in random.sample(ESTIMATION_GROUPS, 2):
            est_count += 1
            group = EstimationItem(
                company_id=COMPANY_ID,
                name=grp_name,
                description=f"Cost estimation group: {grp_name}",
                cost_type="group",
                quantity=0,
                unit="LS",
                unit_cost=0,
                total_cost=0,
                status=random.choice(["incomplete", "complete"]),
                parent_id=None,
                project_id=pid,
            )
            db.add(group)
            db.flush()

            # 3-5 child items per group
            group_total = 0
            for item_name, cost_type, unit in random.sample(ESTIMATION_ITEMS, random.randint(3, 5)):
                est_count += 1
                qty = round(random.uniform(1, 500), 1)
                uc = round(random.uniform(10, 5000), 2)
                tc = round(qty * uc, 2)
                group_total += tc
                child = EstimationItem(
                    company_id=COMPANY_ID,
                    name=item_name,
                    description=f"Estimation for {item_name.lower()}",
                    cost_type=cost_type,
                    quantity=qty,
                    unit=unit,
                    unit_cost=uc,
                    total_cost=tc,
                    status=random.choice(["incomplete", "complete", "not_relevant"]),
                    parent_id=group.id,
                    project_id=pid,
                )
                db.add(child)

            # Update group total
            group.total_cost = round(group_total, 2)

        if pid % 3 == 0:
            db.commit()
    db.commit()
    counts['EstimationItem'] = est_count
    print(f"    Created {est_count} estimation items")

    # S-Curve Data: 100+ (10+ data points per project, weekly snapshots)
    print("  S-Curve Data...")
    scurve_count = 0
    for pid in PROJECT_IDS:
        base_dt = date(2025, 3, 1)
        num_weeks = random.randint(12, 18)
        for week in range(num_weeks):
            scurve_count += 1
            snap_date = base_dt + timedelta(weeks=week)
            pct_progress = min(100.0, round((week / num_weeks) * 100, 1))
            actual_var = round(random.uniform(-8, 5), 1)
            sc = SCurveData(
                company_id=COMPANY_ID,
                project_id=pid,
                date=snap_date,
                planned_physical_pct=pct_progress,
                actual_physical_pct=max(0, min(100, pct_progress + actual_var)),
                revised_physical_pct=max(0, min(100, pct_progress + round(random.uniform(-3, 3), 1))),
                planned_financial_pct=round(pct_progress * random.uniform(0.85, 1.1), 1),
                actual_financial_pct=round(pct_progress * random.uniform(0.8, 1.15), 1),
                manpower_progress_pct=round(pct_progress * random.uniform(0.7, 1.2), 1),
                machinery_progress_pct=round(pct_progress * random.uniform(0.6, 1.1), 1),
                schedule_days_ahead=random.randint(-10, 15),
            )
            db.add(sc)
    db.commit()
    counts['SCurveData'] = scurve_count
    print(f"    Created {scurve_count} S-curve data points")

    # Project Images: 60+
    print("  Project Images...")
    img_count = 0
    for pid in PROJECT_IDS:
        for i in range(random.randint(6, 8)):
            img_count += 1
            idx = i % len(IMAGE_NAMES)
            taken = date(2025, 3, 1) + timedelta(days=random.randint(0, 250))
            img = ProjectImage(
                company_id=COMPANY_ID,
                sequence_name=f"IMG{img_count:05d}",
                name=IMAGE_NAMES[idx],
                description=f"Progress photo: {IMAGE_NAMES[idx].lower()}",
                tags=IMAGE_TAGS_LIST[idx],
                document_id=None,
                file_url=f"/uploads/agcm/photos/2025/{taken.month:02d}/{taken.day:02d}/img_{img_count:05d}.jpg",
                file_name=f"img_{img_count:05d}.jpg",
                display_order=i + 1,
                taken_on=taken,
                project_id=pid,
            )
            db.add(img)
    db.commit()
    counts['ProjectImage'] = img_count
    print(f"    Created {img_count} project images")

    # ==================================================================
    # SUMMARY
    # ==================================================================
    print("\n" + "=" * 60)
    print("SEED DATA SUMMARY — ALL MODULES")
    print("=" * 60)
    total = 0
    for model_name, count in counts.items():
        print(f"  {model_name:<25s} {count:>6d}")
        total += count
    print("  " + "-" * 33)
    print(f"  {'TOTAL':<25s} {total:>6d}")
    print("=" * 60)
    print("Done!")


if __name__ == "__main__":
    seed()
