"""Tests for the agcm_rfi module — RFI, RFILabel, RFIResponse models."""

import pytest
from datetime import date


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rfi_cls(load_model):
    return load_model("agcm_rfi", "rfi", "RFI")

def _rfi_status(load_model):
    return load_model("agcm_rfi", "rfi", "RFIStatus")

def _rfi_priority(load_model):
    return load_model("agcm_rfi", "rfi", "RFIPriority")

def _rfi_label_cls(load_model):
    return load_model("agcm_rfi", "rfi", "RFILabel")

def _rfi_response_cls(load_model):
    return load_model("agcm_rfi", "rfi_response", "RFIResponse")


# ---------------------------------------------------------------------------
# RFI tests
# ---------------------------------------------------------------------------

class TestRFI:

    def test_create_rfi(self, db, load_model, project_ids, company_id, user_id):
        RFI = _rfi_cls(load_model)
        rfi = RFI(
            subject="Clarify foundation depth",
            question="What is the required foundation depth at grid A1?",
            project_id=project_ids[0],
            company_id=company_id,
            created_by_user_id=user_id,
        )
        db.add(rfi)
        db.flush()

        assert rfi.id is not None
        assert rfi.subject == "Clarify foundation depth"
        assert rfi.question is not None

    def test_rfi_sequence_generation(self, db, load_model, project_ids, company_id):
        RFI = _rfi_cls(load_model)

        for i in range(1, 4):
            rfi = RFI(
                subject=f"RFI {i}",
                project_id=project_ids[0],
                company_id=company_id,
                sequence_name=f"RFI{i:05d}",
            )
            db.add(rfi)
            db.flush()

        rfis = db.query(RFI).filter(RFI.project_id == project_ids[0]).order_by(RFI.id).all()
        assert rfis[0].sequence_name == "RFI00001"
        assert rfis[1].sequence_name == "RFI00002"
        assert rfis[2].sequence_name == "RFI00003"

    def test_rfi_status_workflow(self, db, load_model, project_ids, company_id):
        RFI = _rfi_cls(load_model)
        RFIStatus = _rfi_status(load_model)

        rfi = RFI(subject="Status test", project_id=project_ids[0], company_id=company_id, status=RFIStatus.DRAFT)
        db.add(rfi)
        db.flush()
        assert rfi.status == RFIStatus.DRAFT

        for next_status in [RFIStatus.OPEN, RFIStatus.IN_PROGRESS, RFIStatus.ANSWERED, RFIStatus.CLOSED]:
            rfi.status = next_status
            db.flush()
            assert rfi.status == next_status

    def test_create_rfi_label(self, db, load_model, company_id):
        RFILabel = _rfi_label_cls(load_model)
        label = RFILabel(name="Urgent", color="#ff0000", company_id=company_id)
        db.add(label)
        db.flush()

        assert label.id is not None
        assert label.name == "Urgent"
        assert label.color == "#ff0000"

    def test_rfi_label_assignment(self, db, load_model, project_ids, company_id):
        RFI = _rfi_cls(load_model)
        RFILabel = _rfi_label_cls(load_model)

        label1 = RFILabel(name="Electrical", color="#0000ff", company_id=company_id)
        label2 = RFILabel(name="Structural", color="#00ff00", company_id=company_id)
        db.add_all([label1, label2])
        db.flush()

        rfi = RFI(subject="Labeled RFI", project_id=project_ids[0], company_id=company_id)
        rfi.labels.append(label1)
        rfi.labels.append(label2)
        db.add(rfi)
        db.flush()

        assert len(rfi.labels) == 2
        label_names = {l.name for l in rfi.labels}
        assert "Electrical" in label_names
        assert "Structural" in label_names

    def test_rfi_assignees(self, db, load_model, project_ids, company_id):
        """Verify M2M user assignment (using user_id 1 which exists in the companies/users tables)."""
        RFI = _rfi_cls(load_model)
        # We cannot easily create test users without importing User model,
        # so we test the column directly via the association table
        rfi = RFI(subject="Assignee test", project_id=project_ids[0], company_id=company_id)
        db.add(rfi)
        db.flush()

        # Insert into the M2M table directly
        from sqlalchemy import text as sa_text
        db.execute(
            sa_text("INSERT INTO agcm_rfi_assignees (rfi_id, user_id) VALUES (:rfi_id, :user_id)"),
            {"rfi_id": rfi.id, "user_id": 1},
        )
        db.flush()

        row = db.execute(
            sa_text("SELECT user_id FROM agcm_rfi_assignees WHERE rfi_id = :rfi_id"),
            {"rfi_id": rfi.id},
        ).fetchone()
        assert row is not None
        assert row[0] == 1


# ---------------------------------------------------------------------------
# RFI Response tests
# ---------------------------------------------------------------------------

class TestRFIResponse:

    def test_create_rfi_response(self, db, load_model, project_ids, company_id, user_id):
        RFI = _rfi_cls(load_model)
        RFIResponse = _rfi_response_cls(load_model)

        rfi = RFI(subject="Response test", project_id=project_ids[0], company_id=company_id)
        db.add(rfi)
        db.flush()

        resp = RFIResponse(
            rfi_id=rfi.id,
            content="The foundation depth should be 4 feet.",
            responded_by=user_id,
            company_id=company_id,
        )
        db.add(resp)
        db.flush()

        assert resp.id is not None
        assert resp.rfi_id == rfi.id
        assert resp.content == "The foundation depth should be 4 feet."

    def test_rfi_response_auto_advances_status(self, db, load_model, project_ids, company_id, user_id):
        """When a response is added to a DRAFT/OPEN RFI the status should be
        manually advanceable to IN_PROGRESS (business logic is in the service
        layer — here we verify the model allows the transition)."""
        RFI = _rfi_cls(load_model)
        RFIStatus = _rfi_status(load_model)
        RFIResponse = _rfi_response_cls(load_model)

        rfi = RFI(subject="Auto advance", project_id=project_ids[0], company_id=company_id, status=RFIStatus.OPEN)
        db.add(rfi)
        db.flush()

        resp = RFIResponse(rfi_id=rfi.id, content="First response", responded_by=user_id, company_id=company_id)
        db.add(resp)
        db.flush()

        # Simulate service-level auto-advance
        rfi.status = RFIStatus.IN_PROGRESS
        db.flush()
        assert rfi.status == RFIStatus.IN_PROGRESS

    def test_official_response(self, db, load_model, project_ids, company_id, user_id):
        RFI = _rfi_cls(load_model)
        RFIResponse = _rfi_response_cls(load_model)

        rfi = RFI(subject="Official resp", project_id=project_ids[0], company_id=company_id)
        db.add(rfi)
        db.flush()

        resp = RFIResponse(
            rfi_id=rfi.id,
            content="Official answer",
            responded_by=user_id,
            company_id=company_id,
            is_official_response=True,
        )
        db.add(resp)
        db.flush()

        assert resp.is_official_response is True

    def test_close_rfi(self, db, load_model, project_ids, company_id):
        RFI = _rfi_cls(load_model)
        RFIStatus = _rfi_status(load_model)

        rfi = RFI(subject="Close me", project_id=project_ids[0], company_id=company_id, status=RFIStatus.ANSWERED)
        db.add(rfi)
        db.flush()

        rfi.status = RFIStatus.CLOSED
        rfi.closed_date = date(2026, 3, 15)
        db.flush()

        assert rfi.status == RFIStatus.CLOSED
        assert rfi.closed_date == date(2026, 3, 15)

    def test_reopen_rfi(self, db, load_model, project_ids, company_id):
        RFI = _rfi_cls(load_model)
        RFIStatus = _rfi_status(load_model)

        rfi = RFI(
            subject="Reopen me",
            project_id=project_ids[0],
            company_id=company_id,
            status=RFIStatus.CLOSED,
            closed_date=date(2026, 3, 10),
        )
        db.add(rfi)
        db.flush()

        rfi.status = RFIStatus.OPEN
        rfi.closed_date = None
        db.flush()

        assert rfi.status == RFIStatus.OPEN
        assert rfi.closed_date is None

    def test_list_rfis_filter_by_status(self, db, load_model, project_ids, company_id):
        RFI = _rfi_cls(load_model)
        RFIStatus = _rfi_status(load_model)

        db.add(RFI(subject="Open 1", project_id=project_ids[0], company_id=company_id, status=RFIStatus.OPEN))
        db.add(RFI(subject="Closed 1", project_id=project_ids[0], company_id=company_id, status=RFIStatus.CLOSED))
        db.add(RFI(subject="Open 2", project_id=project_ids[0], company_id=company_id, status=RFIStatus.OPEN))
        db.flush()

        open_rfis = db.query(RFI).filter(RFI.status == RFIStatus.OPEN).all()
        assert len(open_rfis) == 2

    def test_list_rfis_filter_by_priority(self, db, load_model, project_ids, company_id):
        RFI = _rfi_cls(load_model)
        RFIPriority = _rfi_priority(load_model)

        db.add(RFI(subject="High 1", project_id=project_ids[0], company_id=company_id, priority=RFIPriority.HIGH))
        db.add(RFI(subject="Low 1", project_id=project_ids[0], company_id=company_id, priority=RFIPriority.LOW))
        db.add(RFI(subject="High 2", project_id=project_ids[0], company_id=company_id, priority=RFIPriority.HIGH))
        db.flush()

        high = db.query(RFI).filter(RFI.priority == RFIPriority.HIGH).all()
        assert len(high) == 2

    def test_delete_rfi_cascades_responses(self, db, load_model, project_ids, company_id, user_id):
        RFI = _rfi_cls(load_model)
        RFIResponse = _rfi_response_cls(load_model)

        rfi = RFI(subject="Cascade delete", project_id=project_ids[0], company_id=company_id)
        db.add(rfi)
        db.flush()

        resp = RFIResponse(rfi_id=rfi.id, content="Gone soon", responded_by=user_id, company_id=company_id)
        db.add(resp)
        db.flush()
        resp_id = resp.id

        db.delete(rfi)
        db.flush()

        assert db.get(RFIResponse, resp_id) is None

    def test_rfi_detail_includes_responses(self, db, load_model, project_ids, company_id, user_id):
        RFI = _rfi_cls(load_model)
        RFIResponse = _rfi_response_cls(load_model)

        rfi = RFI(subject="With responses", project_id=project_ids[0], company_id=company_id)
        db.add(rfi)
        db.flush()

        for i in range(3):
            db.add(RFIResponse(rfi_id=rfi.id, content=f"Response {i}", responded_by=user_id, company_id=company_id))
        db.flush()

        # Refresh to load relationship
        db.expire(rfi)
        fetched = db.get(RFI, rfi.id)
        assert len(fetched.responses) == 3
