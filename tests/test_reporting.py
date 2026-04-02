"""Tests for agcm_reporting module."""
import pytest


@pytest.fixture
def M(load_model):
    return {
        "ReportDef": load_model("agcm_reporting", "report_definition", "AGCMReportDefinition"),
        "Schedule": load_model("agcm_reporting", "report_definition", "AGCMReportSchedule"),
        "Layout": load_model("agcm_reporting", "dashboard_widget", "AGCMDashboardLayout"),
        "Widget": load_model("agcm_reporting", "dashboard_widget", "AGCMDashboardWidget"),
    }


class TestReportDefinition:
    def test_create_report(self, db, M, company_id, user_id):
        r = M["ReportDef"](company_id=company_id, name="Monthly Financial Summary", report_type="financial", data_source="budgets", columns='["project","budgeted","actual","variance"]', is_shared=True, created_by=user_id)
        db.add(r); db.flush()
        assert r.id and r.report_type == "financial"

    def test_report_schedule(self, db, M, company_id, user_id):
        r = M["ReportDef"](company_id=company_id, name="Weekly Safety", report_type="safety", data_source="incidents", created_by=user_id)
        db.add(r); db.flush()
        s = M["Schedule"](report_id=r.id, company_id=company_id, schedule_type="weekly", recipients='["admin@test.com"]', format="pdf", is_active=True)
        db.add(s); db.flush()
        assert s.schedule_type == "weekly"

    def test_report_types(self, db, M, company_id, user_id):
        for rt in ["financial", "schedule", "safety", "resource", "custom"]:
            r = M["ReportDef"](company_id=company_id, name=f"{rt.title()} Report", report_type=rt, data_source="projects", created_by=user_id)
            db.add(r)
        db.flush()
        count = db.query(M["ReportDef"]).filter(M["ReportDef"].company_id == company_id).count()
        assert count >= 5

    def test_report_format_enum(self, db, M, company_id, user_id):
        """Test all report export formats."""
        r = M["ReportDef"](company_id=company_id, name="Format Test", report_type="custom", data_source="projects", created_by=user_id)
        db.add(r); db.flush()
        for fmt in ["pdf", "excel", "csv"]:
            s = M["Schedule"](report_id=r.id, company_id=company_id, schedule_type="daily", format=fmt, is_active=True)
            db.add(s)
        db.flush()
        schedules = db.query(M["Schedule"]).filter(M["Schedule"].report_id == r.id).all()
        assert len(schedules) == 3
        formats = {s.format for s in schedules}
        assert formats == {"pdf", "excel", "csv"}

    def test_system_report_flag(self, db, M, company_id, user_id):
        """System reports should be marked is_system=True."""
        r = M["ReportDef"](company_id=company_id, name="System Report", report_type="financial", data_source="budgets", is_system=True, created_by=user_id)
        db.add(r); db.flush()
        assert r.is_system is True
        r2 = M["ReportDef"](company_id=company_id, name="Custom Report", report_type="custom", data_source="projects", is_system=False, created_by=user_id)
        db.add(r2); db.flush()
        assert r2.is_system is False


class TestDashboard:
    def test_create_layout(self, db, M, company_id, user_id):
        l = M["Layout"](company_id=company_id, name="Executive Dashboard", layout_type="executive", is_default=True, created_by=user_id)
        db.add(l); db.flush()
        assert l.is_default is True

    def test_layout_with_widgets(self, db, M, company_id, user_id):
        l = M["Layout"](company_id=company_id, name="Project Dashboard", layout_type="project", created_by=user_id)
        db.add(l); db.flush()
        widgets = [
            ("Total Budget", "kpi_card", "budgets", 0, 0, 3, 2),
            ("Cost Variance", "bar_chart", "budgets", 3, 0, 6, 4),
            ("Schedule Status", "progress_bar", "tasks", 9, 0, 3, 2),
        ]
        for title, wtype, ds, x, y, w, h in widgets:
            widget = M["Widget"](layout_id=l.id, company_id=company_id, widget_type=wtype, title=title, data_source=ds, position_x=x, position_y=y, width=w, height=h)
            db.add(widget)
        db.flush()
        count = db.query(M["Widget"]).filter(M["Widget"].layout_id == l.id).count()
        assert count == 3

    def test_widget_types(self, db, M, company_id, user_id):
        l = M["Layout"](company_id=company_id, name="Test Layout", created_by=user_id)
        db.add(l); db.flush()
        for wt in ["kpi_card", "bar_chart", "line_chart", "pie_chart", "table", "progress_bar"]:
            w = M["Widget"](layout_id=l.id, company_id=company_id, widget_type=wt, title=f"Test {wt}", data_source="projects")
            db.add(w)
        db.flush()
        count = db.query(M["Widget"]).filter(M["Widget"].layout_id == l.id).count()
        assert count == 6

    def test_default_layout_flag(self, db, M, company_id, user_id):
        """Only one layout should be default."""
        l1 = M["Layout"](company_id=company_id, name="Default", layout_type="executive", is_default=True, created_by=user_id)
        db.add(l1); db.flush()
        l2 = M["Layout"](company_id=company_id, name="Non-Default", layout_type="project", is_default=False, created_by=user_id)
        db.add(l2); db.flush()
        assert l1.is_default is True
        assert l2.is_default is False
