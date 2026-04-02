"""
Seed demo data for agcm_bim module — realistic BIM models, viewpoints, elements,
clash tests, clash results, and 3D annotations.

Run: cd /opt/FastVue/agcm_addons && python scripts/seed_bim_data.py

Assumes:
  - COMPANY_ID=1 and USER_ID=1 already exist
  - Projects with IDs 1-10 already exist (created by agcm seed_demo_data.py)
  - All agcm_bim_* tables already exist (auto-created by AutoSchemaManager)
"""

import json
import os
import sys
import random
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ.setdefault('ENV_FILE', '.env.agcm')

import importlib.util

from app.core.config import settings
from sqlalchemy import create_engine, text, inspect as _inspect
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
db = Session()

COMPANY_ID = 1
USER_ID = 1
PROJECT_IDS = list(range(1, 11))

# ---------------------------------------------------------------------------
# Model loader
# ---------------------------------------------------------------------------
ADDONS_DIR = os.path.join(os.path.dirname(__file__), '..')
_loaded = {}


def load_model(name, path):
    if name in _loaded:
        return _loaded[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    _loaded[name] = mod
    return mod


def mp(module, filename):
    return os.path.abspath(os.path.join(ADDONS_DIR, module, 'models', filename))


# Load models
mod_bim = load_model("_bim_model", mp("agcm_bim", "bim_model.py"))
mod_vp = load_model("_bim_vp", mp("agcm_bim", "bim_viewpoint.py"))
mod_elem = load_model("_bim_elem", mp("agcm_bim", "bim_element.py"))
mod_ann = load_model("_bim_ann", mp("agcm_bim", "annotation.py"))
mod_clash = load_model("_bim_clash", mp("agcm_bim", "clash_detection.py"))

BIMModel = mod_bim.BIMModel
BIMViewpoint = mod_vp.BIMViewpoint
BIMElement = mod_elem.BIMElement
BIMAnnotation3D = mod_ann.BIMAnnotation3D
ClashTest = mod_clash.ClashTest
ClashResult = mod_clash.ClashResult

from app.db.base import Base

# Ensure tables exist
inspector = _inspect(engine)
existing = set(inspector.get_table_names())
needed = ["agcm_bim_models", "agcm_bim_viewpoints", "agcm_bim_elements",
          "agcm_bim_annotations", "agcm_clash_tests", "agcm_clash_results"]
missing = [t for t in needed if t not in existing]
if missing:
    Base.metadata.create_all(bind=engine, tables=[
        Base.metadata.tables[t] for t in missing if t in Base.metadata.tables
    ])

# ---------------------------------------------------------------------------
# Realistic data
# ---------------------------------------------------------------------------

DISCIPLINES = ["architectural", "structural", "mep", "civil", "composite"]

MODEL_TEMPLATES = [
    # (name_template, file_format, discipline, element_count_range)
    ("Architectural Model - {building}", "ifc", "architectural", (500, 2000)),
    ("Structural Model - {building}", "ifc", "structural", (300, 1500)),
    ("MEP Systems - {building}", "ifc", "mep", (800, 3000)),
    ("HVAC Ductwork - {building}", "rvt", "mep", (200, 800)),
    ("Electrical Layout - {building}", "rvt", "mep", (150, 600)),
    ("Plumbing Riser - {building}", "rvt", "mep", (100, 400)),
    ("Civil Grading Plan", "nwd", "civil", (50, 200)),
    ("Site Context Model", "fbx", "civil", (20, 100)),
    ("Interior Visualization", "glb", "architectural", (100, 500)),
    ("Facade Detail Model", "obj", "architectural", (30, 150)),
    ("Structural Steel Framing", "ifc", "structural", (200, 800)),
    ("Fire Protection Layout", "ifc", "mep", (150, 500)),
    ("Foundation Piles Model", "ifc", "structural", (100, 400)),
    ("Landscape & Hardscape", "fbx", "civil", (50, 300)),
    ("Curtain Wall Assembly", "glb", "architectural", (80, 250)),
    ("Composite Coordination", "nwd", "composite", (1000, 5000)),
    ("Roof Framing Plan", "ifc", "structural", (150, 600)),
    ("Stormwater Drainage", "ifc", "mep", (60, 200)),
    ("Elevator Shaft Model", "rvt", "mep", (40, 150)),
    ("Parking Structure", "ifc", "structural", (300, 1200)),
]

BUILDINGS = [
    "Tower A", "Tower B", "Podium", "Basement", "Penthouse",
    "East Wing", "West Wing", "Phase 1", "Phase 2",
]

IFC_TYPES = [
    "IfcWall", "IfcWallStandardCase", "IfcDoor", "IfcWindow", "IfcSlab",
    "IfcColumn", "IfcBeam", "IfcStair", "IfcRailing", "IfcRoof",
    "IfcCovering", "IfcCurtainWall", "IfcPlate", "IfcMember",
    "IfcPipeSegment", "IfcPipeFitting", "IfcDuctSegment", "IfcDuctFitting",
    "IfcFlowTerminal", "IfcFlowController", "IfcCableSegment",
    "IfcLightFixture", "IfcSanitaryTerminal", "IfcFireSuppressionTerminal",
    "IfcFurniture", "IfcBuildingElementProxy",
]

MATERIALS = [
    "Concrete C30/37", "Concrete C40/50", "Steel S355", "Steel S275",
    "Timber GLT", "Aluminum 6063", "Glass 12mm Tempered",
    "Brick Masonry", "Drywall 12.5mm", "Copper Pipe",
    "PVC Pipe", "Galvanized Steel Duct", "Cast Iron",
    "Stainless Steel 316", "Insulation Mineral Wool",
]

LEVELS = [
    "Basement 2", "Basement 1", "Ground Floor", "Level 1", "Level 2",
    "Level 3", "Level 4", "Level 5", "Level 6", "Level 7",
    "Level 8", "Roof", "Mezzanine", "Podium Roof",
]

ANNOTATION_TITLES = [
    "Check rebar spacing at column joint",
    "Duct penetration conflicts with beam",
    "Missing fire stop at floor penetration",
    "Pipe support bracket needed here",
    "Clearance issue — cable tray too close to duct",
    "Verify waterproofing membrane detail",
    "Steel connection detail needs review",
    "Coordination issue between MEP and structure",
    "Access panel required for valve maintenance",
    "Insulation missing on exposed pipe run",
    "Expansion joint alignment check",
    "Foundation settlement crack — investigate",
    "Window frame anchoring detail unclear",
    "Curtain wall bracket location conflict",
    "Electrical panel clearance inadequate",
]


def _random_viewpoint():
    """Generate a random camera position for a viewpoint."""
    return {
        "x": round(random.uniform(-50, 50), 2),
        "y": round(random.uniform(-50, 50), 2),
        "z": round(random.uniform(5, 80), 2),
    }


def _random_bbox():
    """Generate a random bounding box."""
    x = round(random.uniform(0, 100), 2)
    y = round(random.uniform(0, 100), 2)
    z = round(random.uniform(0, 50), 2)
    return json.dumps({
        "min": {"x": x, "y": y, "z": z},
        "max": {"x": x + random.uniform(0.1, 5), "y": y + random.uniform(0.1, 5), "z": z + random.uniform(0.1, 5)},
    })


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------
print("=== Seeding BIM Demo Data ===\n")

model_count = 0
viewpoint_count = 0
element_count = 0
annotation_count = 0
clash_test_count = 0
clash_result_count = 0

model_ids_by_project = {}  # {project_id: [model_ids]}

# --- BIM Models ---
print("Seeding BIM models...")
for pid in PROJECT_IDS:
    model_ids_by_project[pid] = []
    # Each project gets 3-6 models
    num_models = random.randint(3, 6)
    templates = random.sample(MODEL_TEMPLATES, min(num_models, len(MODEL_TEMPLATES)))

    for tmpl_name, fmt, disc, (ec_min, ec_max) in templates:
        building = random.choice(BUILDINGS)
        name = tmpl_name.format(building=building) if "{building}" in tmpl_name else tmpl_name
        ec = random.randint(ec_min, ec_max)
        fsize = random.randint(5_000_000, 500_000_000)

        metadata = json.dumps({
            "units": "meters",
            "application": random.choice(["Revit 2024", "ArchiCAD 27", "Tekla 2024", "OpenBIM"]),
            "schema": "IFC4" if fmt == "ifc" else None,
            "author": random.choice(["Smith & Associates", "BIM Consulting Inc", "Design Team A", "Structural Engineers LLC"]),
            "georeferencing": {"latitude": 25.276987, "longitude": 55.296249, "elevation": 2.5},
        })

        m = BIMModel(
            company_id=COMPANY_ID, project_id=pid,
            sequence_name=f"BIM{model_count + 1:05d}",
            name=name, description=f"3D {disc} model for project {pid}",
            discipline=disc, file_format=fmt,
            file_url=f"/uploads/bim/project_{pid}/{name.lower().replace(' ', '_')}.{fmt}",
            file_name=f"{name.lower().replace(' ', '_')}.{fmt}",
            file_size=fsize,
            xkt_file_url=f"/uploads/bim/project_{pid}/{name.lower().replace(' ', '_')}.xkt" if fmt == "ifc" else None,
            file_size_xkt=int(fsize * 0.3) if fmt == "ifc" else None,
            status="ready",
            version=1, is_current=True,
            element_count=ec, metadata_json=metadata,
            uploaded_by=USER_ID,
        )
        db.add(m)
        db.flush()
        model_ids_by_project[pid].append(m.id)
        model_count += 1

db.commit()
print(f"  BIM Models: {model_count}")

# --- BIM Elements (10-20 per model, sampled) ---
print("Seeding BIM elements...")
all_model_ids = [mid for ids in model_ids_by_project.values() for mid in ids]

for mid in all_model_ids:
    num_elems = random.randint(10, 20)
    for i in range(num_elems):
        elem = BIMElement(
            company_id=COMPANY_ID, model_id=mid,
            global_id=f"{mid:04d}{i:016d}",
            ifc_type=random.choice(IFC_TYPES),
            name=f"Element {i + 1}",
            material=random.choice(MATERIALS),
            level=random.choice(LEVELS),
            discipline=random.choice(DISCIPLINES),
            bounding_box=_random_bbox(),
        )
        db.add(elem)
        element_count += 1

db.commit()
print(f"  BIM Elements: {element_count}")

# --- BIM Viewpoints (2-4 per model) ---
print("Seeding BIM viewpoints...")
for mid in all_model_ids:
    num_vp = random.randint(2, 4)
    vp_names = random.sample([
        "Front Elevation", "Rear Elevation", "Plan View",
        "Section A-A", "Section B-B", "Isometric NE",
        "Isometric SW", "Detail View 1", "Interior Perspective",
        "Bird's Eye", "Foundation Plan", "Roof Plan",
    ], min(num_vp, 12))

    for vp_name in vp_names:
        eye = _random_viewpoint()
        look = _random_viewpoint()
        bcf = json.dumps({
            "perspective_camera": {
                "eye": [eye["x"], eye["y"], eye["z"]],
                "look": [look["x"], look["y"], look["z"]],
                "up": [0, 1, 0],
                "fov": 60,
            },
        })
        vp = BIMViewpoint(
            company_id=COMPANY_ID, model_id=mid,
            name=vp_name,
            description=f"Saved viewpoint: {vp_name}",
            camera_position=json.dumps(eye),
            camera_target=json.dumps(look),
            bcf_data=bcf,
            tags=random.choice(["review", "coordination", "presentation", "documentation"]),
            created_by=USER_ID,
        )
        db.add(vp)
        viewpoint_count += 1

db.commit()
print(f"  BIM Viewpoints: {viewpoint_count}")

# --- Clash Tests (1-2 per project with models >= 2) ---
print("Seeding clash tests & results...")
clash_test_ids = []

for pid, mids in model_ids_by_project.items():
    if len(mids) < 2:
        continue

    num_tests = random.randint(1, min(3, len(mids) - 1))
    model_pairs = []
    for i in range(len(mids)):
        for j in range(i + 1, len(mids)):
            model_pairs.append((mids[i], mids[j]))
    random.shuffle(model_pairs)

    for ma_id, mb_id in model_pairs[:num_tests]:
        test_type = random.choice(["hard", "soft", "clearance"])
        total = random.randint(5, 50)
        crit = random.randint(0, total // 4)
        major = random.randint(0, (total - crit) // 3)
        minor = total - crit - major

        ct = ClashTest(
            company_id=COMPANY_ID, project_id=pid,
            sequence_name=f"CLT{clash_test_count + 1:05d}",
            name=f"Clash Test: Model {ma_id} vs Model {mb_id}",
            description=f"Automated {test_type} clash detection",
            model_a_id=ma_id, model_b_id=mb_id,
            test_type=test_type,
            tolerance=random.choice([0.01, 0.02, 0.05, 0.1]),
            status="completed",
            total_clashes=total,
            critical_count=crit, major_count=major, minor_count=minor,
            run_date=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30)),
            duration_seconds=round(random.uniform(2.5, 120.0), 2),
        )
        db.add(ct)
        db.flush()
        clash_test_ids.append(ct.id)
        clash_test_count += 1

        # Generate clash results
        severities_pool = (["critical"] * crit + ["major"] * major + ["minor"] * minor)
        statuses_pool = ["new", "active", "reviewed", "resolved", "ignored"]

        for k in range(total):
            cr = ClashResult(
                clash_test_id=ct.id, company_id=COMPANY_ID,
                sequence_name=f"CLR{clash_result_count + 1:05d}",
                element_a_id=f"A_{ct.id}_{k:06d}",
                element_a_name=f"Element A-{k}",
                element_a_type=random.choice(IFC_TYPES[:14]),
                element_b_id=f"B_{ct.id}_{k:06d}",
                element_b_name=f"Element B-{k}",
                element_b_type=random.choice(IFC_TYPES[14:]),
                severity=severities_pool[k] if k < len(severities_pool) else "minor",
                status=random.choice(statuses_pool),
                clash_point=json.dumps({
                    "x": round(random.uniform(-30, 30), 3),
                    "y": round(random.uniform(-30, 30), 3),
                    "z": round(random.uniform(0, 30), 3),
                }),
                distance=round(random.uniform(0.001, 0.5), 4),
                description=f"Clash between {random.choice(IFC_TYPES[:14])} and {random.choice(IFC_TYPES[14:])}",
                assigned_to=USER_ID if random.random() < 0.5 else None,
            )
            db.add(cr)
            clash_result_count += 1

db.commit()
print(f"  Clash Tests: {clash_test_count}, Clash Results: {clash_result_count}")

# --- 3D Annotations (2-5 per project) ---
print("Seeding 3D annotations...")
for pid, mids in model_ids_by_project.items():
    if not mids:
        continue

    num_ann = random.randint(2, 5)
    for _ in range(num_ann):
        mid = random.choice(mids)
        pos = _random_viewpoint()
        eye = _random_viewpoint()

        ann = BIMAnnotation3D(
            company_id=COMPANY_ID, project_id=pid,
            model_id=mid,
            world_pos_x=pos["x"], world_pos_y=pos["y"], world_pos_z=pos["z"],
            eye_x=eye["x"], eye_y=eye["y"], eye_z=eye["z"],
            look_x=pos["x"], look_y=pos["y"], look_z=pos["z"],
            entity_id=f"ENTITY_{random.randint(1, 9999):04d}",
            title=random.choice(ANNOTATION_TITLES),
            description=f"Annotation for model {mid} in project {pid}",
            priority=random.choice(["low", "medium", "high", "critical"]),
            status=random.choice(["open", "in_progress", "resolved"]),
            assigned_to=USER_ID if random.random() < 0.6 else None,
            linked_entity_type=random.choice([None, "rfi", "issue", "punch_list"]),
            linked_entity_id=random.randint(1, 50) if random.random() < 0.3 else None,
        )
        db.add(ann)
        annotation_count += 1

db.commit()
print(f"  3D Annotations: {annotation_count}")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n=== BIM Seed Summary ===")
tables = [
    "agcm_bim_models", "agcm_bim_viewpoints", "agcm_bim_elements",
    "agcm_bim_annotations", "agcm_clash_tests", "agcm_clash_results",
]
for t in tables:
    try:
        row = db.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        print(f"  {t}: {row} rows")
    except Exception:
        print(f"  {t}: (table not found)")

print("\nDone!")
db.close()
