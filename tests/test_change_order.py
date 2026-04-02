"""Tests for the agcm_change_order module — ChangeOrder and ChangeOrderLine models."""

import pytest
from datetime import date


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _co(load_model):
    return load_model("agcm_change_order", "change_order", "ChangeOrder")


def _co_line(load_model):
    return load_model("agcm_change_order", "change_order", "ChangeOrderLine")


def _co_status(load_model):
    return load_model("agcm_change_order", "change_order", "ChangeOrderStatus")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestChangeOrder:
    def test_create_change_order(
        self, db, load_model, project_ids, company_id, user_id
    ):
        ChangeOrder = _co(load_model)
        co = ChangeOrder(
            title="Add mezzanine level",
            description="Client requested additional mezzanine between floors 2 and 3",
            reason="Owner change request",
            project_id=project_ids[0],
            company_id=company_id,
            requested_by=user_id,
            requested_date=date(2026, 3, 1),
        )
        db.add(co)
        db.flush()

        assert co.id is not None
        assert co.title == "Add mezzanine level"
        assert co.reason == "Owner change request"

    def test_change_order_sequence(self, db, load_model, project_ids, company_id):
        ChangeOrder = _co(load_model)

        for i in range(1, 4):
            db.add(
                ChangeOrder(
                    title=f"CO {i}",
                    project_id=project_ids[0],
                    company_id=company_id,
                    sequence_name=f"CO{i:05d}",
                )
            )
        db.flush()

        cos = (
            db.query(ChangeOrder)
            .filter(ChangeOrder.project_id == project_ids[0])
            .order_by(ChangeOrder.id)
            .all()
        )
        assert cos[0].sequence_name == "CO00001"
        assert cos[1].sequence_name == "CO00002"
        assert cos[2].sequence_name == "CO00003"

    def test_create_with_lines(self, db, load_model, project_ids, company_id):
        ChangeOrder = _co(load_model)
        ChangeOrderLine = _co_line(load_model)

        co = ChangeOrder(
            title="CO with lines",
            project_id=project_ids[0],
            company_id=company_id,
        )
        db.add(co)
        db.flush()

        lines_data = [
            ("Steel beams", 10, "each", 500.0),
            ("Labor - welding", 40, "hours", 85.0),
            ("Paint", 20, "gallons", 45.0),
        ]
        for desc, qty, unit, cost in lines_data:
            line = ChangeOrderLine(
                change_order_id=co.id,
                description=desc,
                quantity=qty,
                unit=unit,
                unit_cost=cost,
                total_cost=qty * cost,
                company_id=company_id,
            )
            db.add(line)
        db.flush()

        db.expire(co)
        assert len(co.lines) == 3
        assert co.lines[0].description == "Steel beams"
        assert co.lines[1].total_cost == 40 * 85.0

    def test_change_order_approval(
        self, db, load_model, project_ids, company_id, user_id
    ):
        ChangeOrder = _co(load_model)
        ChangeOrderStatus = _co_status(load_model)

        co = ChangeOrder(
            title="Approve me",
            project_id=project_ids[0],
            company_id=company_id,
            status=ChangeOrderStatus.PENDING,
        )
        db.add(co)
        db.flush()

        co.status = ChangeOrderStatus.APPROVED
        co.approved_date = date(2026, 4, 15)
        co.approved_by = user_id
        db.flush()

        assert co.status == ChangeOrderStatus.APPROVED
        assert co.approved_date == date(2026, 4, 15)
        assert co.approved_by == user_id

    def test_change_order_rejection(self, db, load_model, project_ids, company_id):
        ChangeOrder = _co(load_model)
        ChangeOrderStatus = _co_status(load_model)

        co = ChangeOrder(
            title="Reject me",
            project_id=project_ids[0],
            company_id=company_id,
            status=ChangeOrderStatus.PENDING,
        )
        db.add(co)
        db.flush()

        co.status = ChangeOrderStatus.REJECTED
        db.flush()

        assert co.status == ChangeOrderStatus.REJECTED

    def test_line_item_crud(self, db, load_model, project_ids, company_id):
        ChangeOrder = _co(load_model)
        ChangeOrderLine = _co_line(load_model)

        co = ChangeOrder(
            title="Line CRUD", project_id=project_ids[0], company_id=company_id
        )
        db.add(co)
        db.flush()

        # Add
        line = ChangeOrderLine(
            change_order_id=co.id,
            description="Original item",
            quantity=5,
            unit_cost=100.0,
            total_cost=500.0,
            company_id=company_id,
        )
        db.add(line)
        db.flush()
        line_id = line.id
        assert line.id is not None

        # Update
        line.description = "Updated item"
        line.quantity = 10
        line.total_cost = 1000.0
        db.flush()
        refreshed = db.get(ChangeOrderLine, line_id)
        assert refreshed.description == "Updated item"
        assert refreshed.quantity == 10

        # Delete
        db.delete(line)
        db.flush()
        assert db.get(ChangeOrderLine, line_id) is None

    def test_cost_impact_calculation(self, db, load_model, project_ids, company_id):
        ChangeOrder = _co(load_model)

        co = ChangeOrder(
            title="Cost impact test",
            project_id=project_ids[0],
            company_id=company_id,
            cost_impact=75000.50,
            schedule_impact_days=14,
        )
        db.add(co)
        db.flush()

        assert co.cost_impact == 75000.50
        assert co.schedule_impact_days == 14

    def test_list_change_orders_filter(self, db, load_model, project_ids, company_id):
        ChangeOrder = _co(load_model)
        ChangeOrderStatus = _co_status(load_model)

        db.add(
            ChangeOrder(
                title="Draft 1",
                project_id=project_ids[0],
                company_id=company_id,
                status=ChangeOrderStatus.DRAFT,
            )
        )
        db.add(
            ChangeOrder(
                title="Approved 1",
                project_id=project_ids[0],
                company_id=company_id,
                status=ChangeOrderStatus.APPROVED,
            )
        )
        db.add(
            ChangeOrder(
                title="Draft 2",
                project_id=project_ids[0],
                company_id=company_id,
                status=ChangeOrderStatus.DRAFT,
            )
        )
        db.add(
            ChangeOrder(
                title="Void 1",
                project_id=project_ids[0],
                company_id=company_id,
                status=ChangeOrderStatus.VOID,
            )
        )
        db.flush()

        drafts = (
            db.query(ChangeOrder)
            .filter(ChangeOrder.status == ChangeOrderStatus.DRAFT)
            .all()
        )
        assert len(drafts) == 2

    def test_delete_change_order_cascades_lines(
        self, db, load_model, project_ids, company_id
    ):
        ChangeOrder = _co(load_model)
        ChangeOrderLine = _co_line(load_model)

        co = ChangeOrder(
            title="Cascade CO", project_id=project_ids[0], company_id=company_id
        )
        db.add(co)
        db.flush()

        line1 = ChangeOrderLine(
            change_order_id=co.id,
            description="Line 1",
            quantity=1,
            unit_cost=100,
            total_cost=100,
            company_id=company_id,
        )
        line2 = ChangeOrderLine(
            change_order_id=co.id,
            description="Line 2",
            quantity=2,
            unit_cost=200,
            total_cost=400,
            company_id=company_id,
        )
        db.add_all([line1, line2])
        db.flush()
        line_ids = [line1.id, line2.id]

        db.delete(co)
        db.flush()

        for lid in line_ids:
            assert db.get(ChangeOrderLine, lid) is None

    def test_change_order_void(self, db, load_model, project_ids, company_id):
        ChangeOrder = _co(load_model)
        ChangeOrderStatus = _co_status(load_model)

        co = ChangeOrder(
            title="Void test",
            project_id=project_ids[0],
            company_id=company_id,
            status=ChangeOrderStatus.APPROVED,
        )
        db.add(co)
        db.flush()

        co.status = ChangeOrderStatus.VOID
        db.flush()
        assert co.status == ChangeOrderStatus.VOID

    def test_change_order_default_values(self, db, load_model, project_ids, company_id):
        ChangeOrder = _co(load_model)
        ChangeOrderStatus = _co_status(load_model)

        co = ChangeOrder(
            title="Defaults", project_id=project_ids[0], company_id=company_id
        )
        db.add(co)
        db.flush()

        assert co.status == ChangeOrderStatus.DRAFT
        assert co.cost_impact == 0.0
        assert co.schedule_impact_days == 0

    def test_change_order_soft_delete(
        self, db, load_model, project_ids, company_id, user_id
    ):
        """Test soft delete functionality for change orders."""
        ChangeOrder = _co(load_model)

        co = ChangeOrder(
            title="Soft delete test", project_id=project_ids[0], company_id=company_id
        )
        db.add(co)
        db.flush()

        assert co.is_deleted is False
        assert co.deleted_at is None

        co.soft_delete(user_id=user_id)
        db.flush()

        assert co.is_deleted is True
        assert co.deleted_at is not None
        assert co.deleted_by == user_id

    def test_change_order_restore(
        self, db, load_model, project_ids, company_id, user_id
    ):
        """Test restore functionality for change orders."""
        ChangeOrder = _co(load_model)

        co = ChangeOrder(
            title="Restore test", project_id=project_ids[0], company_id=company_id
        )
        db.add(co)
        db.flush()

        co.soft_delete(user_id=user_id)
        db.flush()
        assert co.is_deleted is True

        co.restore()
        db.flush()
        assert co.is_deleted is False
        assert co.deleted_at is None
        assert co.deleted_by is None

    def test_soft_deleted_change_orders_excluded_from_list(
        self, db, load_model, project_ids, company_id, user_id
    ):
        """Test that soft-deleted change orders are excluded from default queries."""
        ChangeOrder = _co(load_model)

        co1 = ChangeOrder(
            title="Active CO", project_id=project_ids[0], company_id=company_id
        )
        co2 = ChangeOrder(
            title="Deleted CO", project_id=project_ids[0], company_id=company_id
        )
        db.add_all([co1, co2])
        db.flush()

        co2.soft_delete(user_id=user_id)
        db.flush()

        active_cos = (
            db.query(ChangeOrder)
            .filter(
                ChangeOrder.project_id == project_ids[0],
                ChangeOrder.is_deleted == False,
            )
            .all()
        )

        assert len(active_cos) == 1
        assert active_cos[0].title == "Active CO"
