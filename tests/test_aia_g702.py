"""
Tests for AIA G702/G703 payment application format.

Verifies:
- PaymentApplication model with G702 fields
- PaymentApplicationLine with G703 fields
- G702 summary computation (contract sum, retainage, payment due)
- Line item totals and pct_complete
"""

import uuid
from datetime import date

import pytest


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


class TestPaymentApplicationG702:

    def test_create_pa_with_g702_fields(self, db, company_id, user_id, load_model):
        PaymentApplication = load_model("agcm_procurement", "payment_application", "PaymentApplication")
        Subcontract = load_model("agcm_procurement", "subcontract", "Subcontract")
        proj = _make_project(db, company_id, user_id, load_model)

        sc = Subcontract(
            company_id=company_id, project_id=proj.id,
            sequence_name=f"SC-{_uid()}", vendor_name="Test Sub",
            status="approved", original_amount=500000,
            revised_amount=525000, created_by=user_id,
        )
        db.add(sc)
        db.flush()

        pa = PaymentApplication(
            company_id=company_id, project_id=proj.id,
            subcontract_id=sc.id, application_number=1,
            period_from=date(2026, 1, 1), period_to=date(2026, 1, 31),
            scheduled_value=525000, retainage_pct=10.0,
            contract_date=date(2025, 6, 15),
            change_order_total=25000,
            created_by=user_id,
        )
        db.add(pa)
        db.flush()

        assert pa.id is not None
        assert pa.retainage_pct == 10.0
        assert pa.change_order_total == 25000
        assert pa.contract_date == date(2025, 6, 15)

    def test_g702_retainage_calculation(self, db, company_id, user_id, load_model):
        """G702: retainage = total_completed × retainage_pct / 100."""
        PaymentApplication = load_model("agcm_procurement", "payment_application", "PaymentApplication")
        Subcontract = load_model("agcm_procurement", "subcontract", "Subcontract")
        proj = _make_project(db, company_id, user_id, load_model)

        sc = Subcontract(
            company_id=company_id, project_id=proj.id,
            sequence_name=f"SC-{_uid()}", vendor_name="Sub",
            status="approved", original_amount=100000,
            created_by=user_id,
        )
        db.add(sc)
        db.flush()

        pa = PaymentApplication(
            company_id=company_id, project_id=proj.id,
            subcontract_id=sc.id, application_number=1,
            period_from=date(2026, 1, 1), period_to=date(2026, 1, 31),
            scheduled_value=100000, total_completed=40000,
            retainage_pct=10.0, created_by=user_id,
        )
        db.add(pa)
        db.flush()

        # G702 computation
        retainage_amount = pa.total_completed * pa.retainage_pct / 100
        assert retainage_amount == 4000.0

        total_earned_less_retainage = pa.total_completed - retainage_amount
        assert total_earned_less_retainage == 36000.0

    def test_g702_current_payment_due(self, db, company_id, user_id, load_model):
        """G702: current_payment = earned_less_retainage - previous_certificates."""
        PaymentApplication = load_model("agcm_procurement", "payment_application", "PaymentApplication")
        Subcontract = load_model("agcm_procurement", "subcontract", "Subcontract")
        proj = _make_project(db, company_id, user_id, load_model)

        sc = Subcontract(
            company_id=company_id, project_id=proj.id,
            sequence_name=f"SC-{_uid()}", vendor_name="Sub",
            status="approved", original_amount=200000,
            created_by=user_id,
        )
        db.add(sc)
        db.flush()

        pa = PaymentApplication(
            company_id=company_id, project_id=proj.id,
            subcontract_id=sc.id, application_number=3,
            period_from=date(2026, 3, 1), period_to=date(2026, 3, 31),
            scheduled_value=200000, total_completed=120000,
            previous_billed=80000, retainage_pct=10.0,
            created_by=user_id,
        )
        db.add(pa)
        db.flush()

        retainage = pa.total_completed * pa.retainage_pct / 100  # 12000
        earned_less_retainage = pa.total_completed - retainage  # 108000
        current_payment_due = earned_less_retainage - pa.previous_billed  # 28000

        assert retainage == 12000.0
        assert earned_less_retainage == 108000.0
        assert current_payment_due == 28000.0


class TestPaymentApplicationLineG703:

    def test_line_with_g703_fields(self, db, company_id, user_id, load_model):
        PaymentApplication = load_model("agcm_procurement", "payment_application", "PaymentApplication")
        PaymentApplicationLine = load_model("agcm_procurement", "payment_application", "PaymentApplicationLine")
        Subcontract = load_model("agcm_procurement", "subcontract", "Subcontract")
        proj = _make_project(db, company_id, user_id, load_model)

        sc = Subcontract(
            company_id=company_id, project_id=proj.id,
            sequence_name=f"SC-{_uid()}", vendor_name="Sub",
            status="approved", original_amount=100000,
            created_by=user_id,
        )
        db.add(sc)
        db.flush()

        pa = PaymentApplication(
            company_id=company_id, project_id=proj.id,
            subcontract_id=sc.id, application_number=1,
            period_from=date(2026, 1, 1), period_to=date(2026, 1, 31),
            scheduled_value=100000, created_by=user_id,
        )
        db.add(pa)
        db.flush()

        line = PaymentApplicationLine(
            application_id=pa.id, company_id=company_id,
            item_number="1",
            description="Concrete Foundation",
            scheduled_value=60000, previous_billed=20000,
            previous_stored_materials=5000,
            current_billed=15000, stored_materials=3000,
            display_order=0,
        )
        db.add(line)
        db.flush()

        assert line.item_number == "1"
        assert line.previous_stored_materials == 5000
        assert line.scheduled_value == 60000

        # G703 total computation
        total_completed = (
            line.previous_billed + line.previous_stored_materials
            + line.current_billed + line.stored_materials
        )
        assert total_completed == 43000  # 20000 + 5000 + 15000 + 3000

        balance = line.scheduled_value - total_completed
        assert balance == 17000

        pct_complete = (total_completed / line.scheduled_value) * 100
        assert round(pct_complete, 1) == 71.7

    def test_multiple_g703_lines_sum(self, db, company_id, user_id, load_model):
        PaymentApplication = load_model("agcm_procurement", "payment_application", "PaymentApplication")
        PaymentApplicationLine = load_model("agcm_procurement", "payment_application", "PaymentApplicationLine")
        Subcontract = load_model("agcm_procurement", "subcontract", "Subcontract")
        proj = _make_project(db, company_id, user_id, load_model)

        sc = Subcontract(
            company_id=company_id, project_id=proj.id,
            sequence_name=f"SC-{_uid()}", vendor_name="Sub",
            status="approved", original_amount=200000,
            created_by=user_id,
        )
        db.add(sc)
        db.flush()

        pa = PaymentApplication(
            company_id=company_id, project_id=proj.id,
            subcontract_id=sc.id, application_number=1,
            period_from=date(2026, 1, 1), period_to=date(2026, 1, 31),
            scheduled_value=200000, created_by=user_id,
        )
        db.add(pa)
        db.flush()

        lines_data = [
            ("1", "Concrete", 80000, 10000, 5000),
            ("2", "Steel", 70000, 8000, 3000),
            ("3", "Drywall", 50000, 5000, 2000),
        ]
        for item_no, desc, sched, current, stored in lines_data:
            db.add(PaymentApplicationLine(
                application_id=pa.id, company_id=company_id,
                item_number=item_no, description=desc,
                scheduled_value=sched, current_billed=current,
                stored_materials=stored, display_order=int(item_no) - 1,
            ))
        db.flush()

        total_scheduled = sum(l.scheduled_value for l in pa.lines)
        total_current = sum(l.current_billed for l in pa.lines)
        total_stored = sum(l.stored_materials for l in pa.lines)

        assert total_scheduled == 200000
        assert total_current == 23000  # 10+8+5
        assert total_stored == 10000   # 5+3+2
