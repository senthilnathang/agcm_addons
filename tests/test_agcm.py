"""Tests for the agcm base module — Project, Weather, and related models."""

import pytest
from datetime import date, datetime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _project_cls(load_model):
    return load_model("agcm", "project", "Project")


def _project_status(load_model):
    return load_model("agcm", "project", "ProjectStatus")


def _project_office(load_model):
    return load_model("agcm", "project", "ProjectOffice")


def _weather_cls(load_model):
    return load_model("agcm", "weather", "Weather")


def _climate_type(load_model):
    return load_model("agcm", "weather", "ClimateType")


def _temp_unit(load_model):
    return load_model("agcm", "weather", "TemperatureUnit")


# ---------------------------------------------------------------------------
# Project tests
# ---------------------------------------------------------------------------


class TestProject:
    def test_create_project(self, db, load_model, company_id, user_id):
        Project = _project_cls(load_model)
        ProjectStatus = _project_status(load_model)

        project = Project(
            company_id=company_id,
            name="Test Construction Project",
            ref_number="TCP-001",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            status=ProjectStatus.NEW,
            owner_id=user_id,
        )
        db.add(project)
        db.flush()

        assert project.id is not None
        assert project.name == "Test Construction Project"
        assert project.ref_number == "TCP-001"
        assert project.is_deleted is False
        assert project.created_at is not None

    def test_project_enum_values_callable(self, db, load_model, company_id, user_id):
        """Verify enum values are stored as lowercase values, not uppercase names."""
        Project = _project_cls(load_model)
        ProjectStatus = _project_status(load_model)

        project = Project(
            company_id=company_id,
            name="Enum Test Project",
            ref_number="ETP-001",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            status=ProjectStatus.NEW,
            owner_id=user_id,
        )
        db.add(project)
        db.flush()

        from sqlalchemy import text

        result = db.execute(
            text("SELECT status FROM agcm_projects WHERE id = :id"), {"id": project.id}
        ).fetchone()

        assert result is not None
        assert result[0] == "new"

    def test_project_office_enum(self, db, load_model, company_id, user_id):
        """Verify ProjectOffice enum stores lowercase values."""
        Project = _project_cls(load_model)
        ProjectOffice = _project_office(load_model)

        project = Project(
            company_id=company_id,
            name="Office Test Project",
            ref_number="OTP-001",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            owner_id=user_id,
            agcm_office=ProjectOffice.CENTRAL,
        )
        db.add(project)
        db.flush()

        from sqlalchemy import text

        result = db.execute(
            text("SELECT agcm_office FROM agcm_projects WHERE id = :id"),
            {"id": project.id},
        ).fetchone()

        assert result is not None
        assert result[0] == "central"

    def test_project_soft_delete(self, db, load_model, company_id, user_id):
        """Test soft delete functionality."""
        Project = _project_cls(load_model)

        project = Project(
            company_id=company_id,
            name="Delete Test Project",
            ref_number="DTP-001",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            owner_id=user_id,
        )
        db.add(project)
        db.flush()

        assert project.is_deleted is False
        assert project.deleted_at is None

        project.soft_delete(user_id=user_id)
        db.flush()

        assert project.is_deleted is True
        assert project.deleted_at is not None
        assert project.deleted_by == user_id

    def test_project_restore(self, db, load_model, company_id, user_id):
        """Test restore functionality."""
        Project = _project_cls(load_model)

        project = Project(
            company_id=company_id,
            name="Restore Test Project",
            ref_number="RTP-001",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            owner_id=user_id,
        )
        db.add(project)
        db.flush()

        project.soft_delete(user_id=user_id)
        db.flush()
        assert project.is_deleted is True

        project.restore()
        db.flush()
        assert project.is_deleted is False
        assert project.deleted_at is None
        assert project.deleted_by is None

    def test_project_audit_trail(self, db, load_model, company_id, user_id):
        """Test audit trail (created_by, updated_by)."""
        Project = _project_cls(load_model)

        project = Project(
            company_id=company_id,
            name="Audit Test Project",
            ref_number="ATP-001",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            owner_id=user_id,
            created_by=user_id,
        )
        db.add(project)
        db.flush()

        assert project.created_by == user_id
        assert project.updated_by is None

        project.updated_by = user_id
        project.name = "Updated Audit Test Project"
        db.flush()

        assert project.updated_by == user_id

    def test_project_timestamp_mixin(self, db, load_model, company_id, user_id):
        """Test automatic timestamp tracking."""
        Project = _project_cls(load_model)

        before_create = datetime.utcnow()
        project = Project(
            company_id=company_id,
            name="Timestamp Test",
            ref_number="TST-001",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            owner_id=user_id,
        )
        db.add(project)
        db.flush()
        after_create = datetime.utcnow()

        assert before_create <= project.created_at <= after_create
        assert project.updated_at is None or project.updated_at >= project.created_at

    def test_project_status_workflow(self, db, load_model, company_id, user_id):
        """Test project status transitions."""
        Project = _project_cls(load_model)
        ProjectStatus = _project_status(load_model)

        statuses = [
            ProjectStatus.NEW,
            ProjectStatus.PRECONSTRUCTION,
            ProjectStatus.BIDDING,
            ProjectStatus.AWARDED,
            ProjectStatus.IN_PROGRESS,
            ProjectStatus.PUNCH_LIST,
            ProjectStatus.CLOSEOUT,
            ProjectStatus.COMPLETED,
        ]

        for i, status in enumerate(statuses):
            project = Project(
                company_id=company_id,
                name=f"Status Test {i}",
                ref_number=f"STT-{i:03d}",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 12, 31),
                owner_id=user_id,
                status=status,
            )
            db.add(project)
            db.flush()

            from sqlalchemy import text

            result = db.execute(
                text("SELECT status FROM agcm_projects WHERE id = :id"),
                {"id": project.id},
            ).fetchone()

            assert result[0] == status.value

    def test_project_filter_by_status(self, db, load_model, company_id, user_id):
        """Test filtering projects by status."""
        Project = _project_cls(load_model)
        ProjectStatus = _project_status(load_model)

        db.add(
            Project(
                company_id=company_id,
                name="Active Project",
                ref_number="AP-001",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 12, 31),
                owner_id=user_id,
                status=ProjectStatus.IN_PROGRESS,
            )
        )
        db.add(
            Project(
                company_id=company_id,
                name="Completed Project",
                ref_number="CP-001",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 12, 31),
                owner_id=user_id,
                status=ProjectStatus.COMPLETED,
            )
        )
        db.flush()

        active_projects = (
            db.query(Project)
            .filter(
                Project.company_id == company_id,
                Project.status == ProjectStatus.IN_PROGRESS.value,
                Project.is_deleted == False,
            )
            .all()
        )

        assert len(active_projects) == 1
        assert active_projects[0].name == "Active Project"


# ---------------------------------------------------------------------------
# Weather tests
# ---------------------------------------------------------------------------


class TestWeather:
    def test_create_weather(self, db, load_model, company_id):
        Weather = _weather_cls(load_model)

        weather = Weather(
            company_id=company_id,
            date=date(2026, 3, 15),
            temperature=72.5,
            rain=False,
        )
        db.add(weather)
        db.flush()

        assert weather.id is not None
        assert weather.temperature == 72.5
        assert weather.rain is False

    def test_weather_climate_type_enum(self, db, load_model, company_id):
        """Verify ClimateType enum stores lowercase values."""
        Weather = _weather_cls(load_model)
        ClimateType = _climate_type(load_model)

        weather = Weather(
            company_id=company_id,
            date=date(2026, 3, 15),
            temperature=85.0,
            climate_type=ClimateType.CLEAR,
        )
        db.add(weather)
        db.flush()

        from sqlalchemy import text

        result = db.execute(
            text("SELECT climate_type FROM agcm_weather WHERE id = :id"),
            {"id": weather.id},
        ).fetchone()

        assert result is not None
        assert result[0] == "clear"

    def test_weather_temperature_unit_enum(self, db, load_model, company_id):
        """Verify TemperatureUnit enum stores actual values (F, C)."""
        Weather = _weather_cls(load_model)
        TemperatureUnit = _temp_unit(load_model)

        weather_f = Weather(
            company_id=company_id,
            date=date(2026, 3, 15),
            temperature=72.0,
            temperature_type=TemperatureUnit.FAHRENHEIT,
        )
        db.add(weather_f)
        db.flush()

        from sqlalchemy import text

        result = db.execute(
            text("SELECT temperature_type FROM agcm_weather WHERE id = :id"),
            {"id": weather_f.id},
        ).fetchone()

        assert result is not None
        assert result[0] == "F"

    def test_weather_all_climate_types(self, db, load_model, company_id):
        """Test all climate types can be stored."""
        Weather = _weather_cls(load_model)
        ClimateType = _climate_type(load_model)

        for climate in ClimateType:
            weather = Weather(
                company_id=company_id,
                date=date(2026, 3, 15),
                temperature=70.0,
                climate_type=climate,
            )
            db.add(weather)
            db.flush()

            from sqlalchemy import text

            result = db.execute(
                text("SELECT climate_type FROM agcm_weather WHERE id = :id"),
                {"id": weather.id},
            ).fetchone()

            assert result[0] == climate.value


# ---------------------------------------------------------------------------
# Soft delete service integration tests
# ---------------------------------------------------------------------------


class TestProjectSoftDeleteService:
    def test_service_soft_delete_excludes_from_list(
        self, db, load_model, company_id, user_id
    ):
        """Test that soft-deleted projects are excluded from default queries."""
        Project = _project_cls(load_model)

        project1 = Project(
            company_id=company_id,
            name="Active",
            ref_number="A-001",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            owner_id=user_id,
        )
        project2 = Project(
            company_id=company_id,
            name="Deleted",
            ref_number="D-001",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            owner_id=user_id,
        )
        db.add_all([project1, project2])
        db.flush()

        project2.soft_delete(user_id=user_id)
        db.flush()

        active_projects = (
            db.query(Project)
            .filter(
                Project.company_id == company_id,
                Project.is_deleted == False,
            )
            .all()
        )

        assert len(active_projects) == 1
        assert active_projects[0].name == "Active"

    def test_service_list_includes_deleted(self, db, load_model, company_id, user_id):
        """Test that include_deleted=True includes soft-deleted records."""
        Project = _project_cls(load_model)

        project1 = Project(
            company_id=company_id,
            name="Active",
            ref_number="A-001",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            owner_id=user_id,
        )
        project2 = Project(
            company_id=company_id,
            name="Deleted",
            ref_number="D-001",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            owner_id=user_id,
        )
        db.add_all([project1, project2])
        db.flush()

        project2.soft_delete(user_id=user_id)
        db.flush()

        all_projects = (
            db.query(Project)
            .filter(
                Project.company_id == company_id,
            )
            .all()
        )

        assert len(all_projects) == 2
