"""
Tests for project-level access control.

Verifies:
- ProjectMember model CRUD
- Role hierarchy (owner > manager > member > viewer)
- get_user_project_ids filtering
- has_project_access checks
- check_project_role with min_role
"""

import importlib.util
import os
import sys
import types
import uuid
from datetime import date

import pytest

ADDONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if "addons" not in sys.modules:
    addons_pkg = types.ModuleType("addons")
    addons_pkg.__path__ = [ADDONS_DIR]
    addons_pkg.__package__ = "addons"
    sys.modules["addons"] = addons_pkg

# Load access helper
_access_mod = importlib.util.spec_from_file_location(
    "agcm_project_access",
    os.path.join(ADDONS_DIR, "agcm", "services", "project_access.py"),
)
_access = importlib.util.module_from_spec(_access_mod)
sys.modules["agcm_project_access"] = _access
_access_mod.loader.exec_module(_access)

get_user_project_ids = _access.get_user_project_ids
has_project_access = _access.has_project_access
get_project_role = _access.get_project_role
check_project_role = _access.check_project_role


def _uid():
    return uuid.uuid4().hex[:8]


def _make_project(db, company_id, user_id, load_model):
    Project = load_model("agcm", "project", "Project")
    proj = Project(
        company_id=company_id, name=f"Test-{_uid()}", ref_number=f"TP-{_uid()}",
        start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        status="new", owner_id=user_id,
    )
    db.add(proj)
    db.flush()
    return proj


class TestProjectMemberModel:

    def test_create_project_member(self, db, company_id, user_id, load_model):
        ProjectMember = load_model("agcm", "project_member", "ProjectMember")
        proj = _make_project(db, company_id, user_id, load_model)

        member = ProjectMember(
            project_id=proj.id, user_id=user_id, company_id=company_id,
            role="owner", assigned_by=user_id,
        )
        db.add(member)
        db.flush()

        assert member.id is not None
        assert member.role == "owner"
        assert member.is_active is True

    def test_multiple_roles_per_project(self, db, company_id, user_id, load_model):
        """Different users can have different roles in same project."""
        from sqlalchemy import text
        ProjectMember = load_model("agcm", "project_member", "ProjectMember")
        proj = _make_project(db, company_id, user_id, load_model)

        # Create a second user
        db.execute(text(
            "INSERT INTO users (id, email, username, full_name, hashed_password, "
            "is_active, is_verified, is_superuser, is_deleted, "
            "failed_login_attempts, must_change_password, two_factor_enabled, "
            "backup_codes, message_ids, follower_ids, metadata_json, tags, version) "
            "VALUES (2, 'user2@test.com', 'user2', 'User Two', 'pw', "
            "true, true, false, false, 0, false, false, "
            "'[]'::json, '[]'::json, '[]'::json, '{}'::json, '[]'::json, 1) "
            "ON CONFLICT (id) DO NOTHING"
        ))
        db.flush()

        m1 = ProjectMember(
            project_id=proj.id, user_id=user_id, company_id=company_id,
            role="owner", assigned_by=user_id,
        )
        m2 = ProjectMember(
            project_id=proj.id, user_id=2, company_id=company_id,
            role="viewer", assigned_by=user_id,
        )
        db.add_all([m1, m2])
        db.flush()

        assert m1.role == "owner"
        assert m2.role == "viewer"


class TestProjectAccessHelpers:

    def test_get_user_project_ids(self, db, company_id, user_id, load_model):
        ProjectMember = load_model("agcm", "project_member", "ProjectMember")
        p1 = _make_project(db, company_id, user_id, load_model)
        p2 = _make_project(db, company_id, user_id, load_model)

        db.add(ProjectMember(project_id=p1.id, user_id=user_id, company_id=company_id, role="manager"))
        db.add(ProjectMember(project_id=p2.id, user_id=user_id, company_id=company_id, role="viewer"))
        db.flush()

        ids = get_user_project_ids(db, user_id, company_id)
        assert p1.id in ids
        assert p2.id in ids

    def test_get_user_project_ids_with_min_role(self, db, company_id, user_id, load_model):
        ProjectMember = load_model("agcm", "project_member", "ProjectMember")
        p1 = _make_project(db, company_id, user_id, load_model)
        p2 = _make_project(db, company_id, user_id, load_model)

        db.add(ProjectMember(project_id=p1.id, user_id=user_id, company_id=company_id, role="manager"))
        db.add(ProjectMember(project_id=p2.id, user_id=user_id, company_id=company_id, role="viewer"))
        db.flush()

        # min_role=manager should only return p1
        ids = get_user_project_ids(db, user_id, company_id, min_role="manager")
        assert p1.id in ids
        assert p2.id not in ids

    def test_has_project_access(self, db, company_id, user_id, load_model):
        ProjectMember = load_model("agcm", "project_member", "ProjectMember")
        proj = _make_project(db, company_id, user_id, load_model)

        db.add(ProjectMember(project_id=proj.id, user_id=user_id, company_id=company_id, role="member"))
        db.flush()

        assert has_project_access(db, user_id, proj.id) is True
        assert has_project_access(db, 9999, proj.id) is False

    def test_check_project_role_hierarchy(self, db, company_id, user_id, load_model):
        ProjectMember = load_model("agcm", "project_member", "ProjectMember")
        proj = _make_project(db, company_id, user_id, load_model)

        db.add(ProjectMember(project_id=proj.id, user_id=user_id, company_id=company_id, role="manager"))
        db.flush()

        # Manager is >= viewer, member, manager but < owner
        assert check_project_role(db, user_id, proj.id, min_role="viewer") is True
        assert check_project_role(db, user_id, proj.id, min_role="member") is True
        assert check_project_role(db, user_id, proj.id, min_role="manager") is True
        assert check_project_role(db, user_id, proj.id, min_role="owner") is False

    def test_get_project_role(self, db, company_id, user_id, load_model):
        ProjectMember = load_model("agcm", "project_member", "ProjectMember")
        proj = _make_project(db, company_id, user_id, load_model)

        db.add(ProjectMember(project_id=proj.id, user_id=user_id, company_id=company_id, role="owner"))
        db.flush()

        assert get_project_role(db, user_id, proj.id) == "owner"
        assert get_project_role(db, 9999, proj.id) is None

    def test_inactive_member_excluded(self, db, company_id, user_id, load_model):
        ProjectMember = load_model("agcm", "project_member", "ProjectMember")
        proj = _make_project(db, company_id, user_id, load_model)

        m = ProjectMember(project_id=proj.id, user_id=user_id, company_id=company_id, role="member", is_active=False)
        db.add(m)
        db.flush()

        assert has_project_access(db, user_id, proj.id) is False
        assert get_user_project_ids(db, user_id, company_id) == []
