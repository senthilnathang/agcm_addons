"""
Seed demo approval chains for AGCM construction entities.

Creates multi-step approval workflows for:
- Purchase Orders (2-step: PM → VP, amount-based routing)
- Change Orders (2-step: Project Engineer → PM)
- Subcontracts (2-step: Procurement Mgr → Director)

Usage:
    cd /opt/FastVue/backend
    source .venv/bin/activate
    ENV_FILE=.env.agcm python -c "from agcm_addons.agcm.scripts.seed_approval_chains import seed; seed()"
"""

import os
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend"))
ADDONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if ADDONS_DIR not in sys.path:
    sys.path.insert(0, ADDONS_DIR)

os.environ.setdefault("ENV_FILE", ".env.agcm")


def seed(db=None, company_id=1, user_id=1):
    """Seed approval chains for AGCM entities."""
    close_db = False
    if db is None:
        from app.core.config import settings
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
        Session = sessionmaker(bind=engine)
        db = Session()
        close_db = True

    try:
        from modules.base_automation.models.approval import ApprovalChain, ApprovalStep

        # Check if chains already exist
        existing = db.query(ApprovalChain).filter(
            ApprovalChain.company_id == company_id,
            ApprovalChain.entity_type.in_(["purchase_order", "change_order", "subcontract"]),
        ).count()
        if existing > 0:
            print(f"Approval chains already exist ({existing} found) — skipping seed")
            return

        # --- 1. Purchase Order Approval (2-step) ---
        po_chain = ApprovalChain(
            name="PO Approval — Standard",
            code=f"agcm_po_approval_{company_id}",
            entity_type="purchase_order",
            chain_type="sequential",
            default_sla_hours=48,
            notify_on_pending=True,
            notify_on_complete=True,
            is_active=True,
            priority=10,
            company_id=company_id,
        )
        db.add(po_chain)
        db.flush()

        db.add(ApprovalStep(
            chain_id=po_chain.id,
            step_order=1,
            name="Project Manager Review",
            approver_type="user",
            approver_id=user_id,
            sla_hours=24,
            required_count=1,
            is_active=True,
        ))
        db.add(ApprovalStep(
            chain_id=po_chain.id,
            step_order=2,
            name="VP Approval",
            approver_type="user",
            approver_id=user_id,
            sla_hours=48,
            required_count=1,
            is_active=True,
        ))
        print(f"  Created PO approval chain: {po_chain.name}")

        # --- 2. Change Order Approval (2-step) ---
        co_chain = ApprovalChain(
            name="Change Order Approval",
            code=f"agcm_co_approval_{company_id}",
            entity_type="change_order",
            chain_type="sequential",
            default_sla_hours=72,
            notify_on_pending=True,
            notify_on_complete=True,
            is_active=True,
            priority=10,
            company_id=company_id,
        )
        db.add(co_chain)
        db.flush()

        db.add(ApprovalStep(
            chain_id=co_chain.id,
            step_order=1,
            name="Project Engineer Review",
            approver_type="user",
            approver_id=user_id,
            sla_hours=24,
            required_count=1,
            is_active=True,
        ))
        db.add(ApprovalStep(
            chain_id=co_chain.id,
            step_order=2,
            name="Project Manager Approval",
            approver_type="user",
            approver_id=user_id,
            sla_hours=48,
            required_count=1,
            is_active=True,
        ))
        print(f"  Created CO approval chain: {co_chain.name}")

        # --- 3. Subcontract Approval (2-step) ---
        sc_chain = ApprovalChain(
            name="Subcontract Approval",
            code=f"agcm_sc_approval_{company_id}",
            entity_type="subcontract",
            chain_type="sequential",
            default_sla_hours=72,
            notify_on_pending=True,
            notify_on_complete=True,
            is_active=True,
            priority=10,
            company_id=company_id,
        )
        db.add(sc_chain)
        db.flush()

        db.add(ApprovalStep(
            chain_id=sc_chain.id,
            step_order=1,
            name="Procurement Manager Review",
            approver_type="user",
            approver_id=user_id,
            sla_hours=24,
            required_count=1,
            is_active=True,
        ))
        db.add(ApprovalStep(
            chain_id=sc_chain.id,
            step_order=2,
            name="Director Approval",
            approver_type="user",
            approver_id=user_id,
            sla_hours=72,
            required_count=1,
            is_active=True,
        ))
        print(f"  Created SC approval chain: {sc_chain.name}")

        db.commit()
        print("Approval chain seeding complete — 3 chains, 6 steps")

    except ImportError as e:
        print(f"Cannot seed approval chains: {e}")
    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    seed()
