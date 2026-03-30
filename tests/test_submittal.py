"""Tests for the agcm_submittal module — Submittal, SubmittalPackage, SubmittalType,
SubmittalLabel, SubmittalApprover models."""

import pytest
from datetime import date, datetime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _submittal(load_model):
    return load_model("agcm_submittal", "submittal", "Submittal")

def _submittal_status(load_model):
    return load_model("agcm_submittal", "submittal", "SubmittalStatus")

def _submittal_priority(load_model):
    return load_model("agcm_submittal", "submittal", "SubmittalPriority")

def _submittal_package(load_model):
    return load_model("agcm_submittal", "submittal", "SubmittalPackage")

def _submittal_type(load_model):
    return load_model("agcm_submittal", "submittal", "SubmittalType")

def _submittal_label(load_model):
    return load_model("agcm_submittal", "submittal", "SubmittalLabel")

def _submittal_approver(load_model):
    return load_model("agcm_submittal", "submittal", "SubmittalApprover")

def _approver_status(load_model):
    return load_model("agcm_submittal", "submittal", "ApproverStatus")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSubmittalType:

    def test_create_submittal_type(self, db, load_model, company_id):
        SubmittalType = _submittal_type(load_model)
        st = SubmittalType(name="Shop Drawings", company_id=company_id)
        db.add(st)
        db.flush()

        assert st.id is not None
        assert st.name == "Shop Drawings"


class TestSubmittalPackage:

    def test_create_submittal_package(self, db, load_model, project_ids, company_id):
        SubmittalPackage = _submittal_package(load_model)
        pkg = SubmittalPackage(
            name="Structural Steel Package",
            description="All structural steel submittals",
            project_id=project_ids[0],
            company_id=company_id,
        )
        db.add(pkg)
        db.flush()

        assert pkg.id is not None
        assert pkg.name == "Structural Steel Package"


class TestSubmittal:

    def test_create_submittal(self, db, load_model, project_ids, company_id, user_id):
        Submittal = _submittal(load_model)
        SubmittalStatus = _submittal_status(load_model)
        SubmittalPriority = _submittal_priority(load_model)

        sub = Submittal(
            title="Steel Connection Details",
            description="Shop drawings for moment connections",
            spec_section="05 12 00",
            status=SubmittalStatus.DRAFT,
            priority=SubmittalPriority.HIGH,
            revision=1,
            due_date=date(2026, 6, 15),
            project_id=project_ids[0],
            company_id=company_id,
            submitted_by=user_id,
            sequence_name="SUB00001",
        )
        db.add(sub)
        db.flush()

        assert sub.id is not None
        assert sub.title == "Steel Connection Details"
        assert sub.status == SubmittalStatus.DRAFT
        assert sub.priority == SubmittalPriority.HIGH
        assert sub.sequence_name == "SUB00001"

    def test_submittal_sequence(self, db, load_model, project_ids, company_id):
        Submittal = _submittal(load_model)

        for i in range(1, 4):
            db.add(Submittal(
                title=f"Sub {i}",
                project_id=project_ids[0],
                company_id=company_id,
                sequence_name=f"SUB{i:05d}",
            ))
        db.flush()

        subs = db.query(Submittal).filter(Submittal.project_id == project_ids[0]).order_by(Submittal.id).all()
        assert subs[0].sequence_name == "SUB00001"
        assert subs[1].sequence_name == "SUB00002"
        assert subs[2].sequence_name == "SUB00003"

    def test_submittal_approval_workflow(self, db, load_model, project_ids, company_id, user_id):
        Submittal = _submittal(load_model)
        SubmittalStatus = _submittal_status(load_model)
        SubmittalApprover = _submittal_approver(load_model)
        ApproverStatus = _approver_status(load_model)

        sub = Submittal(title="Approval flow", project_id=project_ids[0], company_id=company_id, status=SubmittalStatus.PENDING_REVIEW)
        db.add(sub)
        db.flush()

        app1 = SubmittalApprover(submittal_id=sub.id, user_id=user_id, sequence=1, status=ApproverStatus.PENDING, company_id=company_id)
        app2 = SubmittalApprover(submittal_id=sub.id, user_id=user_id, sequence=2, status=ApproverStatus.PENDING, company_id=company_id)
        db.add_all([app1, app2])
        db.flush()

        # First approver approves
        app1.status = ApproverStatus.APPROVED
        app1.signed_at = datetime(2026, 4, 1, 10, 0)
        db.flush()
        assert app1.status == ApproverStatus.APPROVED

        # Second approver approves
        app2.status = ApproverStatus.APPROVED
        app2.signed_at = datetime(2026, 4, 2, 14, 0)
        sub.status = SubmittalStatus.APPROVED
        db.flush()

        assert sub.status == SubmittalStatus.APPROVED
        assert all(a.status == ApproverStatus.APPROVED for a in [app1, app2])

    def test_submittal_rejection(self, db, load_model, project_ids, company_id, user_id):
        Submittal = _submittal(load_model)
        SubmittalStatus = _submittal_status(load_model)
        SubmittalApprover = _submittal_approver(load_model)
        ApproverStatus = _approver_status(load_model)

        sub = Submittal(title="Will reject", project_id=project_ids[0], company_id=company_id, status=SubmittalStatus.IN_REVIEW)
        db.add(sub)
        db.flush()

        app1 = SubmittalApprover(submittal_id=sub.id, user_id=user_id, sequence=1, status=ApproverStatus.PENDING, company_id=company_id)
        db.add(app1)
        db.flush()

        app1.status = ApproverStatus.REJECTED
        app1.comments = "Does not meet spec requirements"
        sub.status = SubmittalStatus.REJECTED
        db.flush()

        assert sub.status == SubmittalStatus.REJECTED
        assert app1.comments == "Does not meet spec requirements"

    def test_submittal_resubmit(self, db, load_model, project_ids, company_id):
        Submittal = _submittal(load_model)
        SubmittalStatus = _submittal_status(load_model)

        sub = Submittal(title="Resubmit test", project_id=project_ids[0], company_id=company_id, status=SubmittalStatus.REJECTED, revision=1)
        db.add(sub)
        db.flush()

        sub.status = SubmittalStatus.RESUBMITTED
        sub.revision += 1
        db.flush()

        assert sub.status == SubmittalStatus.RESUBMITTED
        assert sub.revision == 2

    def test_submittal_label_assignment(self, db, load_model, project_ids, company_id):
        Submittal = _submittal(load_model)
        SubmittalLabel = _submittal_label(load_model)

        lbl1 = SubmittalLabel(name="Mechanical", color="#ff6600", company_id=company_id)
        lbl2 = SubmittalLabel(name="Critical Path", color="#ff0000", company_id=company_id)
        db.add_all([lbl1, lbl2])
        db.flush()

        sub = Submittal(title="Labeled sub", project_id=project_ids[0], company_id=company_id)
        sub.labels.append(lbl1)
        sub.labels.append(lbl2)
        db.add(sub)
        db.flush()

        assert len(sub.labels) == 2

    def test_list_submittals_filter(self, db, load_model, project_ids, company_id):
        Submittal = _submittal(load_model)
        SubmittalStatus = _submittal_status(load_model)
        SubmittalPriority = _submittal_priority(load_model)

        db.add(Submittal(title="Draft 1", project_id=project_ids[0], company_id=company_id, status=SubmittalStatus.DRAFT, priority=SubmittalPriority.LOW))
        db.add(Submittal(title="Approved 1", project_id=project_ids[0], company_id=company_id, status=SubmittalStatus.APPROVED, priority=SubmittalPriority.HIGH))
        db.add(Submittal(title="Draft 2", project_id=project_ids[0], company_id=company_id, status=SubmittalStatus.DRAFT, priority=SubmittalPriority.HIGH))
        db.flush()

        drafts = db.query(Submittal).filter(Submittal.status == SubmittalStatus.DRAFT).all()
        assert len(drafts) == 2

        high_pri = db.query(Submittal).filter(Submittal.priority == SubmittalPriority.HIGH).all()
        assert len(high_pri) == 2

    def test_delete_submittal_cascades(self, db, load_model, project_ids, company_id, user_id):
        Submittal = _submittal(load_model)
        SubmittalApprover = _submittal_approver(load_model)

        sub = Submittal(title="Cascade del", project_id=project_ids[0], company_id=company_id)
        db.add(sub)
        db.flush()

        app1 = SubmittalApprover(submittal_id=sub.id, user_id=user_id, sequence=1, company_id=company_id)
        db.add(app1)
        db.flush()
        app_id = app1.id

        db.delete(sub)
        db.flush()

        assert db.get(SubmittalApprover, app_id) is None
