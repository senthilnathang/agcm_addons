"""Tests for agcm_resource module."""
import pytest
from datetime import date, datetime


@pytest.fixture
def M(load_model):
    return {
        "Worker": load_model("agcm_resource", "worker", "Worker"),
        "Equipment": load_model("agcm_resource", "equipment", "Equipment"),
        "Timesheet": load_model("agcm_resource", "timesheet", "Timesheet"),
        "Assignment": load_model("agcm_resource", "equipment_assignment", "EquipmentAssignment"),
    }


class TestWorker:
    def test_create_worker(self, db, M, company_id):
        w = M["Worker"](company_id=company_id, sequence_name="WRK00001", first_name="John", last_name="Smith", full_name="John Smith", trade="electrician", hourly_rate=75, status="active")
        db.add(w); db.flush()
        assert w.id and w.trade == "electrician"

    def test_worker_skills(self, db, M, company_id):
        w = M["Worker"](company_id=company_id, first_name="Jane", last_name="Doe", full_name="Jane Doe", skill_level="journeyman", status="active")
        db.add(w); db.flush()
        assert w.skill_level == "journeyman"

    def test_worker_status(self, db, M, company_id):
        w = M["Worker"](company_id=company_id, first_name="Bob", last_name="T", full_name="Bob T", status="active")
        db.add(w); db.flush()
        w.status = "on_leave"; db.flush()
        assert w.status == "on_leave"


class TestEquipment:
    def test_create_equipment(self, db, M, company_id, project_ids):
        e = M["Equipment"](company_id=company_id, sequence_name="EQP00001", name="CAT 320 Excavator", equipment_type="excavator", status="available", daily_rate=2500)
        db.add(e); db.flush()
        assert e.id and e.daily_rate == 2500

    def test_equipment_assignment(self, db, M, company_id, project_ids):
        e = M["Equipment"](company_id=company_id, name="Crane", equipment_type="crane", status="available")
        db.add(e); db.flush()
        a = M["Assignment"](company_id=company_id, equipment_id=e.id, project_id=project_ids[0], assigned_date=date.today(), daily_rate=3500, total_days=10, total_cost=35000)
        db.add(a); db.flush()
        assert a.total_cost == 35000


class TestTimesheet:
    def test_create_timesheet(self, db, M, company_id, project_ids):
        w = M["Worker"](company_id=company_id, first_name="Tim", last_name="S", full_name="Tim S", hourly_rate=45, overtime_rate=67.50, status="active")
        db.add(w); db.flush()
        ts = M["Timesheet"](company_id=company_id, worker_id=w.id, project_id=project_ids[0], date=date.today(), regular_hours=8, overtime_hours=2, total_hours=10, regular_cost=360, overtime_cost=135, total_cost=495, status="draft")
        db.add(ts); db.flush()
        assert ts.total_hours == 10 and ts.total_cost == 495

    def test_timesheet_approval(self, db, M, company_id, user_id, project_ids):
        w = M["Worker"](company_id=company_id, first_name="A", last_name="B", full_name="A B", status="active")
        db.add(w); db.flush()
        ts = M["Timesheet"](company_id=company_id, worker_id=w.id, project_id=project_ids[0], date=date.today(), regular_hours=8, status="draft")
        db.add(ts); db.flush()
        ts.status = "submitted"; db.flush()
        ts.status = "approved"; ts.approved_by = user_id; db.flush()
        assert ts.status == "approved"

    def test_timesheet_cost_calc(self, db, M, company_id, project_ids):
        w = M["Worker"](company_id=company_id, first_name="C", last_name="D", full_name="C D", hourly_rate=50, overtime_rate=75, status="active")
        db.add(w); db.flush()
        reg, ot = 8, 4
        ts = M["Timesheet"](company_id=company_id, worker_id=w.id, project_id=project_ids[0], date=date.today(), regular_hours=reg, overtime_hours=ot, total_hours=reg+ot, regular_cost=reg*50, overtime_cost=ot*75, total_cost=reg*50+ot*75, status="draft")
        db.add(ts); db.flush()
        assert ts.regular_cost == 400 and ts.overtime_cost == 300 and ts.total_cost == 700
