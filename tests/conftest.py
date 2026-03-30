"""
Test configuration and shared fixtures for AGCM addon module tests.

Uses importlib to load model classes by file path, avoiding the need for
the FastVue AddonNamespaceFinder that is only active at runtime.
"""

import importlib.util
import os
import sys
from datetime import date

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
ADDONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if ADDONS_DIR not in sys.path:
    sys.path.insert(0, ADDONS_DIR)

# Ensure settings can load — set required env vars for the Settings class
# before importing anything from app.*
os.environ.setdefault("ENV_FILE", ".env.agcm")
os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5433")
os.environ.setdefault("POSTGRES_USER", "girdersoft")
os.environ.setdefault("POSTGRES_PASSWORD", "girdersoft")
os.environ.setdefault("POSTGRES_DB", "fastvue_test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")

from app.db.base import Base  # noqa: E402

# ---------------------------------------------------------------------------
# importlib model loader (same pattern as seed_all_modules.py)
# ---------------------------------------------------------------------------
_loaded_modules: dict = {}


def _load_module(module_name: str, file_path: str):
    """Load a Python file via importlib and cache it."""
    if module_name in _loaded_modules:
        return _loaded_modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    _loaded_modules[module_name] = mod
    return mod


def _model_path(addon_module: str, filename: str) -> str:
    """Return absolute path to a model file inside an addon module."""
    return os.path.abspath(os.path.join(ADDONS_DIR, addon_module, "models", filename))


def _core_model_path(rel_path: str) -> str:
    """Return absolute path to a core backend model file."""
    return os.path.abspath(os.path.join(BACKEND_DIR, rel_path))


# ---------------------------------------------------------------------------
# Pre-load all model files so that Base.metadata knows every table.
# Order matters: core models first, then base agcm, then 7 addon modules.
# ---------------------------------------------------------------------------

# Core backend models required by FK references from agcm models
_core_models = [
    ("documents_space", _core_model_path("modules/documents/models/space.py")),
    ("documents_folder", _core_model_path("modules/documents/models/folder.py")),
    ("documents_document", _core_model_path("modules/documents/models/document.py")),
    ("documents_tag", _core_model_path("modules/documents/models/tag.py")),
    ("documents_link", _core_model_path("modules/documents/models/link.py")),
    ("documents_version", _core_model_path("modules/documents/models/version.py")),
    ("documents_share", _core_model_path("modules/documents/models/share.py")),
]

# Base AGCM models required by FK references
_base_models = [
    ("agcm_lookups", _model_path("agcm", "lookups.py")),
    ("agcm_project", _model_path("agcm", "project.py")),
    ("agcm_weather", _model_path("agcm", "weather.py")),
    ("agcm_daily_activity_log", _model_path("agcm", "daily_activity_log.py")),
    ("agcm_manpower", _model_path("agcm", "manpower.py")),
    ("agcm_photo", _model_path("agcm", "photo.py")),
    ("agcm_notes", _model_path("agcm", "notes.py")),
    ("agcm_visitor", _model_path("agcm", "visitor.py")),
    ("agcm_safety_violation", _model_path("agcm", "safety_violation.py")),
    ("agcm_delay", _model_path("agcm", "delay.py")),
    ("agcm_inspection", _model_path("agcm", "inspection.py")),
    ("agcm_deficiency", _model_path("agcm", "deficiency.py")),
    ("agcm_accident", _model_path("agcm", "accident.py")),
]

_addon_models = [
    # agcm_document
    ("agcm_document_folder", _model_path("agcm_document", "folder.py")),
    ("agcm_document_document", _model_path("agcm_document", "document.py")),
    # agcm_rfi
    ("agcm_rfi_rfi", _model_path("agcm_rfi", "rfi.py")),
    ("agcm_rfi_rfi_response", _model_path("agcm_rfi", "rfi_response.py")),
    # agcm_submittal
    ("agcm_submittal_submittal", _model_path("agcm_submittal", "submittal.py")),
    # agcm_change_order
    ("agcm_change_order_change_order", _model_path("agcm_change_order", "change_order.py")),
    # agcm_schedule
    ("agcm_schedule_schedule", _model_path("agcm_schedule", "schedule.py")),
    ("agcm_schedule_wbs", _model_path("agcm_schedule", "wbs.py")),
    ("agcm_schedule_task", _model_path("agcm_schedule", "task.py")),
    ("agcm_schedule_dependency", _model_path("agcm_schedule", "dependency.py")),
    # agcm_finance
    ("agcm_finance_cost_code", _model_path("agcm_finance", "cost_code.py")),
    ("agcm_finance_budget", _model_path("agcm_finance", "budget.py")),
    ("agcm_finance_expense", _model_path("agcm_finance", "expense.py")),
    ("agcm_finance_invoice", _model_path("agcm_finance", "invoice.py")),
    ("agcm_finance_bill", _model_path("agcm_finance", "bill.py")),
    # agcm_progress
    ("agcm_progress_milestone", _model_path("agcm_progress", "milestone.py")),
    ("agcm_progress_issue", _model_path("agcm_progress", "issue.py")),
    ("agcm_progress_estimation", _model_path("agcm_progress", "estimation.py")),
    ("agcm_progress_scurve", _model_path("agcm_progress", "scurve.py")),
    ("agcm_progress_project_image", _model_path("agcm_progress", "project_image.py")),
    # agcm_estimate
    ("agcm_estimate_cost_catalog", _model_path("agcm_estimate", "cost_catalog.py")),
    ("agcm_estimate_assembly", _model_path("agcm_estimate", "assembly.py")),
    ("agcm_estimate_estimate", _model_path("agcm_estimate", "estimate.py")),
    ("agcm_estimate_estimate_markup", _model_path("agcm_estimate", "estimate_markup.py")),
    ("agcm_estimate_proposal", _model_path("agcm_estimate", "proposal.py")),
    ("agcm_estimate_takeoff", _model_path("agcm_estimate", "takeoff.py")),
    # agcm_procurement
    ("agcm_procurement_purchase_order", _model_path("agcm_procurement", "purchase_order.py")),
    ("agcm_procurement_subcontract", _model_path("agcm_procurement", "subcontract.py")),
    ("agcm_procurement_vendor_bill", _model_path("agcm_procurement", "vendor_bill.py")),
]

for mod_name, mod_path in _core_models + _base_models + _addon_models:
    if os.path.exists(mod_path):
        _load_module(mod_name, mod_path)


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "postgresql://girdersoft:girdersoft@localhost:5433/fastvue_test"


@pytest.fixture(scope="session")
def engine():
    """Create test engine, create all tables, yield, then drop all tables."""
    eng = create_engine(TEST_DATABASE_URL, echo=False)

    # Drop everything first to handle stale enum types from previous runs
    with eng.connect() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO PUBLIC"))
        conn.commit()

    # Create all tables known to Base.metadata
    Base.metadata.create_all(bind=eng)

    yield eng

    # Drop tables — use raw SQL CASCADE to handle circular FK deps
    # (companies <-> users have mutual FK references)
    with eng.connect() as conn:
        # Get all table names from our metadata and drop with CASCADE
        for table in reversed(Base.metadata.sorted_tables):
            try:
                conn.execute(text(f'DROP TABLE IF EXISTS "{table.name}" CASCADE'))
            except Exception:
                pass
        conn.commit()
    eng.dispose()


@pytest.fixture(scope="function")
def db(engine):
    """
    Transaction-isolated database session.

    Each test runs inside a transaction that is rolled back at the end,
    ensuring complete test isolation without needing to recreate tables.
    """
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection, join_transaction_mode="create_savepoint")
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# _ensure_company_and_user — seed prerequisite rows via raw SQL
# ---------------------------------------------------------------------------

def _ensure_company_and_user(db, company_id: int, user_id: int):
    """Insert a company and user row if they do not already exist.

    Uses raw SQL to avoid needing the full Company/User ORM models
    (which drag in many dependencies).
    """
    exists = db.execute(
        text("SELECT 1 FROM companies WHERE id = :id"), {"id": company_id}
    ).fetchone()
    if not exists:
        db.execute(text(
            "INSERT INTO companies (id, name, code, is_active, is_headquarters) "
            "VALUES (:id, :name, :code, true, true)"
        ), {"id": company_id, "name": "Test Company", "code": "TEST"})

    exists = db.execute(
        text("SELECT 1 FROM users WHERE id = :id"), {"id": user_id}
    ).fetchone()
    if not exists:
        db.execute(text(
            "INSERT INTO users (id, email, username, full_name, hashed_password, "
            "is_active, is_verified, is_superuser, is_deleted, "
            "failed_login_attempts, must_change_password, two_factor_enabled, "
            "backup_codes, message_ids, follower_ids, metadata_json, tags, version) "
            "VALUES (:id, :email, :username, :full_name, :pw, "
            "true, true, false, false, 0, false, false, "
            "'[]'::json, '[]'::json, '[]'::json, '{}'::json, '[]'::json, 1)"
        ), {
            "id": user_id,
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "pw": "not-a-real-hash",
        })
    db.flush()


# ---------------------------------------------------------------------------
# Convenience scalar fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def company_id(db):
    """Return company_id=1, ensuring the company row exists."""
    cid = 1
    uid = 1
    _ensure_company_and_user(db, cid, uid)
    return cid


@pytest.fixture
def user_id(db):
    """Return user_id=1, ensuring the user row exists."""
    cid = 1
    uid = 1
    _ensure_company_and_user(db, cid, uid)
    return uid


# ---------------------------------------------------------------------------
# load_model fixture — resolves a model class by addon module / file / class
# ---------------------------------------------------------------------------

@pytest.fixture
def load_model():
    """
    Return a callable that loads a model class by (addon_module, file_name, class_name).

    Usage::

        ProjectFolder = load_model("agcm_document", "folder", "ProjectFolder")
    """

    def _load(addon_module: str, file_name: str, class_name: str):
        cache_key = f"{addon_module}_{file_name}"
        path = _model_path(addon_module, f"{file_name}.py")
        mod = _load_module(cache_key, path)
        return getattr(mod, class_name)

    return _load


# ---------------------------------------------------------------------------
# project_ids fixture — creates 3 lightweight test projects
# ---------------------------------------------------------------------------

@pytest.fixture
def project_ids(db, company_id, user_id):
    """Create prerequisite company/user rows, then 3 test projects."""
    _ensure_company_and_user(db, company_id, user_id)

    Project = _loaded_modules["agcm_project"].Project

    ids = []
    for i in range(1, 4):
        proj = Project(
            company_id=company_id,
            name=f"Test Project {i}",
            ref_number=f"TP-{i:04d}",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            status="new",
            owner_id=user_id,
        )
        db.add(proj)
        db.flush()
        ids.append(proj.id)

    return ids
