"""Tests for the agcm_progress module — Milestone, Issue, EstimationItem,
SCurveData, ProjectImage models."""

import pytest
from datetime import date


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _milestone(load_model):
    return load_model("agcm_progress", "milestone", "Milestone")

def _issue(load_model):
    return load_model("agcm_progress", "issue", "Issue")

def _issue_severity(load_model):
    return load_model("agcm_progress", "issue", "IssueSeverity")

def _issue_status(load_model):
    return load_model("agcm_progress", "issue", "IssueStatus")

def _issue_priority(load_model):
    return load_model("agcm_progress", "issue", "IssuePriority")

def _estimation(load_model):
    return load_model("agcm_progress", "estimation", "EstimationItem")

def _cost_type(load_model):
    return load_model("agcm_progress", "estimation", "CostType")

def _estimation_status(load_model):
    return load_model("agcm_progress", "estimation", "EstimationStatus")

def _scurve(load_model):
    return load_model("agcm_progress", "scurve", "SCurveData")

def _project_image(load_model):
    return load_model("agcm_progress", "project_image", "ProjectImage")


# ---------------------------------------------------------------------------
# Milestone tests
# ---------------------------------------------------------------------------

class TestMilestone:

    def test_create_milestone(self, db, load_model, project_ids, company_id):
        Milestone = _milestone(load_model)

        ms = Milestone(
            name="Foundation Complete",
            description="All foundation work finished",
            planned_date=date(2026, 5, 1),
            project_id=project_ids[0],
            company_id=company_id,
            sequence_name="MS00001",
        )
        db.add(ms)
        db.flush()

        assert ms.id is not None
        assert ms.name == "Foundation Complete"
        assert ms.planned_date == date(2026, 5, 1)
        assert ms.is_completed is False

    def test_milestone_sequence(self, db, load_model, project_ids, company_id):
        Milestone = _milestone(load_model)

        for i in range(1, 4):
            db.add(Milestone(
                name=f"Milestone {i}",
                project_id=project_ids[0],
                company_id=company_id,
                sequence_name=f"MS{i:05d}",
            ))
        db.flush()

        mss = db.query(Milestone).filter(Milestone.project_id == project_ids[0]).order_by(Milestone.id).all()
        assert mss[0].sequence_name == "MS00001"
        assert mss[2].sequence_name == "MS00003"

    def test_toggle_milestone_completed(self, db, load_model, project_ids, company_id):
        Milestone = _milestone(load_model)

        ms = Milestone(name="Toggle test", project_id=project_ids[0], company_id=company_id, is_completed=False)
        db.add(ms)
        db.flush()
        assert ms.is_completed is False

        ms.is_completed = True
        ms.actual_date = date(2026, 4, 28)
        db.flush()
        assert ms.is_completed is True

        ms.is_completed = False
        ms.actual_date = None
        db.flush()
        assert ms.is_completed is False

    def test_delete_milestone(self, db, load_model, project_ids, company_id):
        Milestone = _milestone(load_model)

        ms = Milestone(name="Delete me", project_id=project_ids[0], company_id=company_id)
        db.add(ms)
        db.flush()
        ms_id = ms.id

        db.delete(ms)
        db.flush()
        assert db.get(Milestone, ms_id) is None


# ---------------------------------------------------------------------------
# Issue tests
# ---------------------------------------------------------------------------

class TestIssue:

    def test_create_issue(self, db, load_model, project_ids, company_id):
        Issue = _issue(load_model)
        IssueSeverity = _issue_severity(load_model)
        IssuePriority = _issue_priority(load_model)

        issue = Issue(
            title="Crack in foundation wall",
            description="Hairline crack observed at grid B3",
            severity=IssueSeverity.MAJOR,
            priority=IssuePriority.HIGH,
            location="Grid B3, Level 0",
            project_id=project_ids[0],
            company_id=company_id,
            sequence_name="ISS00001",
        )
        db.add(issue)
        db.flush()

        assert issue.id is not None
        assert issue.severity == IssueSeverity.MAJOR
        assert issue.priority == IssuePriority.HIGH

    def test_issue_sequence(self, db, load_model, project_ids, company_id):
        Issue = _issue(load_model)

        for i in range(1, 4):
            db.add(Issue(
                title=f"Issue {i}",
                project_id=project_ids[0],
                company_id=company_id,
                sequence_name=f"ISS{i:05d}",
            ))
        db.flush()

        issues = db.query(Issue).filter(Issue.project_id == project_ids[0]).order_by(Issue.id).all()
        assert issues[0].sequence_name == "ISS00001"
        assert issues[2].sequence_name == "ISS00003"

    def test_issue_resolve(self, db, load_model, project_ids, company_id):
        Issue = _issue(load_model)
        IssueStatus = _issue_status(load_model)

        issue = Issue(title="Resolve me", project_id=project_ids[0], company_id=company_id, status=IssueStatus.IN_PROGRESS)
        db.add(issue)
        db.flush()

        issue.status = IssueStatus.RESOLVED
        issue.resolved_date = date(2026, 4, 10)
        db.flush()

        assert issue.status == IssueStatus.RESOLVED
        assert issue.resolved_date == date(2026, 4, 10)

    def test_issue_close(self, db, load_model, project_ids, company_id):
        Issue = _issue(load_model)
        IssueStatus = _issue_status(load_model)

        issue = Issue(title="Close me", project_id=project_ids[0], company_id=company_id, status=IssueStatus.RESOLVED)
        db.add(issue)
        db.flush()

        issue.status = IssueStatus.CLOSED
        db.flush()
        assert issue.status == IssueStatus.CLOSED

    def test_list_issues_filter(self, db, load_model, project_ids, company_id):
        Issue = _issue(load_model)
        IssueSeverity = _issue_severity(load_model)
        IssueStatus = _issue_status(load_model)

        db.add(Issue(title="Critical open", project_id=project_ids[0], company_id=company_id, severity=IssueSeverity.CRITICAL, status=IssueStatus.OPEN))
        db.add(Issue(title="Minor open", project_id=project_ids[0], company_id=company_id, severity=IssueSeverity.MINOR, status=IssueStatus.OPEN))
        db.add(Issue(title="Critical closed", project_id=project_ids[0], company_id=company_id, severity=IssueSeverity.CRITICAL, status=IssueStatus.CLOSED))
        db.add(Issue(title="Major open", project_id=project_ids[0], company_id=company_id, severity=IssueSeverity.MAJOR, status=IssueStatus.OPEN))
        db.flush()

        critical = db.query(Issue).filter(Issue.severity == IssueSeverity.CRITICAL).all()
        assert len(critical) == 2

        open_issues = db.query(Issue).filter(Issue.status == IssueStatus.OPEN).all()
        assert len(open_issues) == 3

    def test_issue_status_workflow(self, db, load_model, project_ids, company_id):
        Issue = _issue(load_model)
        IssueStatus = _issue_status(load_model)

        issue = Issue(title="Workflow", project_id=project_ids[0], company_id=company_id, status=IssueStatus.OPEN)
        db.add(issue)
        db.flush()

        for st in [IssueStatus.IN_PROGRESS, IssueStatus.RESOLVED, IssueStatus.CLOSED]:
            issue.status = st
            db.flush()
            assert issue.status == st


# ---------------------------------------------------------------------------
# Estimation tests
# ---------------------------------------------------------------------------

class TestEstimation:

    def test_create_estimation_item(self, db, load_model, project_ids, company_id):
        EstimationItem = _estimation(load_model)
        CostType = _cost_type(load_model)

        item = EstimationItem(
            name="Concrete Works",
            cost_type=CostType.MATERIAL,
            quantity=500,
            unit="CY",
            unit_cost=180.0,
            total_cost=90000.0,
            project_id=project_ids[0],
            company_id=company_id,
        )
        db.add(item)
        db.flush()

        assert item.id is not None
        assert item.cost_type == CostType.MATERIAL
        assert item.total_cost == 90000.0

    def test_estimation_hierarchy(self, db, load_model, project_ids, company_id):
        EstimationItem = _estimation(load_model)
        CostType = _cost_type(load_model)

        parent = EstimationItem(
            name="Structural Group",
            cost_type=CostType.GROUP,
            total_cost=0,
            project_id=project_ids[0],
            company_id=company_id,
        )
        db.add(parent)
        db.flush()

        child1 = EstimationItem(
            name="Steel beams",
            cost_type=CostType.MATERIAL,
            quantity=100,
            unit_cost=500,
            total_cost=50000,
            project_id=project_ids[0],
            company_id=company_id,
            parent_id=parent.id,
        )
        child2 = EstimationItem(
            name="Welding labor",
            cost_type=CostType.LABOR,
            quantity=200,
            unit="hours",
            unit_cost=75,
            total_cost=15000,
            project_id=project_ids[0],
            company_id=company_id,
            parent_id=parent.id,
        )
        db.add_all([child1, child2])
        db.flush()

        assert child1.parent_id == parent.id
        assert child2.parent_id == parent.id

    def test_estimation_rollup(self, db, load_model, project_ids, company_id):
        """Verify that children totals can be summed for parent rollup."""
        EstimationItem = _estimation(load_model)
        CostType = _cost_type(load_model)
        from sqlalchemy import func as sa_func

        parent = EstimationItem(name="Group", cost_type=CostType.GROUP, total_cost=0, project_id=project_ids[0], company_id=company_id)
        db.add(parent)
        db.flush()

        db.add(EstimationItem(name="C1", cost_type=CostType.MATERIAL, total_cost=30000, project_id=project_ids[0], company_id=company_id, parent_id=parent.id))
        db.add(EstimationItem(name="C2", cost_type=CostType.LABOR, total_cost=20000, project_id=project_ids[0], company_id=company_id, parent_id=parent.id))
        db.add(EstimationItem(name="C3", cost_type=CostType.EQUIPMENT, total_cost=10000, project_id=project_ids[0], company_id=company_id, parent_id=parent.id))
        db.flush()

        rollup = db.query(sa_func.sum(EstimationItem.total_cost)).filter(EstimationItem.parent_id == parent.id).scalar()
        assert rollup == 60000

        # Update parent total with rollup
        parent.total_cost = rollup
        db.flush()
        assert parent.total_cost == 60000

    def test_estimation_cost_types(self, db, load_model, project_ids, company_id):
        EstimationItem = _estimation(load_model)
        CostType = _cost_type(load_model)

        for ct in CostType:
            item = EstimationItem(name=f"Item {ct.value}", cost_type=ct, project_id=project_ids[0], company_id=company_id)
            db.add(item)
            db.flush()
            assert item.cost_type == ct


# ---------------------------------------------------------------------------
# S-Curve tests
# ---------------------------------------------------------------------------

class TestSCurve:

    def test_create_scurve_data(self, db, load_model, project_ids, company_id):
        SCurveData = _scurve(load_model)

        pt = SCurveData(
            project_id=project_ids[0],
            company_id=company_id,
            date=date(2026, 3, 1),
            planned_physical_pct=25.0,
            actual_physical_pct=22.0,
            revised_physical_pct=24.0,
            planned_financial_pct=20.0,
            actual_financial_pct=18.0,
            manpower_progress_pct=30.0,
            machinery_progress_pct=15.0,
            schedule_days_ahead=-3,
        )
        db.add(pt)
        db.flush()

        assert pt.id is not None
        assert pt.planned_physical_pct == 25.0
        assert pt.schedule_days_ahead == -3

    def test_scurve_chart_data(self, db, load_model, project_ids, company_id):
        SCurveData = _scurve(load_model)

        dates_data = [
            (date(2026, 1, 1), 0, 0),
            (date(2026, 2, 1), 10, 8),
            (date(2026, 3, 1), 25, 22),
            (date(2026, 4, 1), 45, 40),
            (date(2026, 5, 1), 65, 60),
        ]
        for d, planned, actual in dates_data:
            db.add(SCurveData(
                project_id=project_ids[0],
                company_id=company_id,
                date=d,
                planned_physical_pct=planned,
                actual_physical_pct=actual,
            ))
        db.flush()

        chart = (
            db.query(SCurveData)
            .filter(SCurveData.project_id == project_ids[0])
            .order_by(SCurveData.date)
            .all()
        )
        assert len(chart) == 5
        assert chart[0].date < chart[-1].date
        assert chart[0].planned_physical_pct == 0
        assert chart[-1].planned_physical_pct == 65

    def test_scurve_unique_constraint(self, db, load_model, project_ids, company_id):
        """Same project + date should violate unique constraint."""
        SCurveData = _scurve(load_model)

        db.add(SCurveData(project_id=project_ids[0], company_id=company_id, date=date(2026, 6, 1)))
        db.flush()

        db.add(SCurveData(project_id=project_ids[0], company_id=company_id, date=date(2026, 6, 1)))
        with pytest.raises(Exception):
            db.flush()
        db.rollback()


# ---------------------------------------------------------------------------
# ProjectImage tests
# ---------------------------------------------------------------------------

class TestProjectImage:

    def test_create_project_image(self, db, load_model, project_ids, company_id):
        ProjectImage = _project_image(load_model)

        img = ProjectImage(
            name="Foundation pour progress",
            description="Photo showing 50% completion of foundation pour",
            tags="foundation,concrete,progress",
            file_url="/uploads/agcm/photos/2026/03/30/img001.jpg",
            file_name="img001.jpg",
            display_order=1,
            taken_on=date(2026, 3, 30),
            project_id=project_ids[0],
            company_id=company_id,
            sequence_name="IMG00001",
        )
        db.add(img)
        db.flush()

        assert img.id is not None
        assert img.name == "Foundation pour progress"
        assert img.tags == "foundation,concrete,progress"
        assert img.taken_on == date(2026, 3, 30)

    def test_list_project_images(self, db, load_model, project_ids, company_id):
        ProjectImage = _project_image(load_model)

        for i in range(5):
            db.add(ProjectImage(
                name=f"Image {i}",
                display_order=i,
                project_id=project_ids[0],
                company_id=company_id,
            ))
        db.flush()

        images = (
            db.query(ProjectImage)
            .filter(ProjectImage.project_id == project_ids[0])
            .order_by(ProjectImage.display_order)
            .all()
        )
        assert len(images) == 5
        assert images[0].display_order == 0
        assert images[4].display_order == 4

    def test_project_image_update(self, db, load_model, project_ids, company_id):
        ProjectImage = _project_image(load_model)

        img = ProjectImage(name="Original", project_id=project_ids[0], company_id=company_id)
        db.add(img)
        db.flush()

        img.name = "Renamed"
        img.description = "Added description"
        db.flush()

        refreshed = db.get(ProjectImage, img.id)
        assert refreshed.name == "Renamed"
        assert refreshed.description == "Added description"
