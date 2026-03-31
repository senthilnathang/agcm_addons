"""Tests for agcm_safety module."""
import pytest
from datetime import date


@pytest.fixture
def M(load_model):
    return {
        "Template": load_model("agcm_safety", "checklist", "ChecklistTemplate"),
        "TemplateItem": load_model("agcm_safety", "checklist", "ChecklistTemplateItem"),
        "Inspection": load_model("agcm_safety", "inspection", "SafetyInspection"),
        "InspectionItem": load_model("agcm_safety", "inspection", "SafetyInspectionItem"),
        "PunchItem": load_model("agcm_safety", "punch_list", "PunchListItem"),
        "Incident": load_model("agcm_safety", "incident", "IncidentReport"),
    }


class TestChecklist:
    def test_create_template(self, db, M, company_id):
        t = M["Template"](company_id=company_id, name="Foundation Inspection", category="structural", is_active=True)
        db.add(t); db.flush()
        assert t.id and t.category == "structural"

    def test_template_with_items(self, db, M, company_id):
        t = M["Template"](company_id=company_id, name="Framing Checklist", category="structural")
        db.add(t); db.flush()
        for i, desc in enumerate(["Check stud spacing", "Verify header size", "Inspect connections"]):
            item = M["TemplateItem"](template_id=t.id, description=desc, required=True, display_order=i, company_id=company_id)
            db.add(item)
        db.flush()
        count = db.query(M["TemplateItem"]).filter(M["TemplateItem"].template_id == t.id).count()
        assert count == 3


class TestInspection:
    def test_create_inspection(self, db, M, company_id, project_ids):
        insp = M["Inspection"](company_id=company_id, project_id=project_ids[0], sequence_name="INSP00001", inspector_name="John Inspector", inspection_type="foundation", status="scheduled", scheduled_date=date(2025, 4, 1))
        db.add(insp); db.flush()
        assert insp.status == "scheduled"

    def test_inspection_workflow(self, db, M, company_id, project_ids):
        insp = M["Inspection"](company_id=company_id, project_id=project_ids[0], sequence_name="INSP00002", inspector_name="Jane", inspection_type="electrical", status="scheduled")
        db.add(insp); db.flush()
        insp.status = "in_progress"; db.flush()
        insp.status = "passed"; insp.completed_date = date.today(); insp.overall_result = "pass"; db.flush()
        assert insp.status == "passed"

    def test_inspection_items(self, db, M, company_id, project_ids):
        insp = M["Inspection"](company_id=company_id, project_id=project_ids[0], sequence_name="INSP00003", inspector_name="Bob", inspection_type="plumbing", status="in_progress")
        db.add(insp); db.flush()
        item = M["InspectionItem"](inspection_id=insp.id, company_id=company_id, description="Check pipe joints", result="pass")
        db.add(item); db.flush()
        assert item.result == "pass"


class TestPunchList:
    def test_create_punch_item(self, db, M, company_id, project_ids):
        p = M["PunchItem"](company_id=company_id, project_id=project_ids[0], sequence_name="PL00001", title="Paint touch-up in lobby", status="open", priority="medium", location="Lobby")
        db.add(p); db.flush()
        assert p.status == "open"

    def test_punch_item_workflow(self, db, M, company_id, user_id, project_ids):
        p = M["PunchItem"](company_id=company_id, project_id=project_ids[0], sequence_name="PL00002", title="Fix door", status="open", priority="high")
        db.add(p); db.flush()
        p.status = "in_progress"; p.assigned_to = user_id; db.flush()
        p.status = "completed"; p.completed_date = date.today(); db.flush()
        p.status = "verified"; p.verified_by = user_id; p.verified_date = date.today(); db.flush()
        assert p.status == "verified"


class TestIncident:
    def test_create_incident(self, db, M, company_id, user_id, project_ids):
        inc = M["Incident"](company_id=company_id, project_id=project_ids[0], sequence_name="INC00001", title="Worker slip on wet floor", description="Worker slipped in lobby area", severity="first_aid", status="reported", incident_date=date.today(), reported_by=user_id)
        db.add(inc); db.flush()
        assert inc.severity == "first_aid"

    def test_incident_investigation(self, db, M, company_id, user_id, project_ids):
        inc = M["Incident"](company_id=company_id, project_id=project_ids[0], sequence_name="INC00002", title="Near miss", severity="near_miss", status="reported", incident_date=date.today(), description="Object fell", reported_by=user_id)
        db.add(inc); db.flush()
        inc.status = "investigating"; inc.investigated_by = user_id; inc.investigation_date = date.today(); db.flush()
        inc.root_cause = "Unsecured material on scaffold"; inc.corrective_action = "Implement toe boards"; db.flush()
        inc.status = "closed"; inc.closed_date = date.today(); db.flush()
        assert inc.status == "closed" and inc.root_cause is not None
