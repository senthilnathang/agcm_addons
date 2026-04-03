"""Submittal service - business logic for construction submittals"""

import logging
import re
from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from addons.agcm_submittal.models.submittal import (
    Submittal,
    SubmittalApprover,
    SubmittalLabel,
    SubmittalPackage,
    SubmittalStatus,
    SubmittalType,
    agcm_submittal_label_rel,
    ApproverStatus,
)
from addons.agcm_submittal.schemas.submittal import (
    SubmittalCreate,
    SubmittalUpdate,
    SubmittalPackageCreate,
    SubmittalTypeCreate,
    SubmittalLabelCreate,
)

logger = logging.getLogger(__name__)


class SubmittalService:
    """Handles Submittal CRUD and approval workflow."""

    def __init__(self, db: Session, company_id: int, user_id: int):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id

    # ------------------------------------------------------------------
    # Sequence generation
    # ------------------------------------------------------------------

    def _next_sequence(self) -> str:
        """Generate next submittal sequence: SUB00001, SUB00002, etc."""
        last = (
            self.db.query(Submittal.sequence_name)
            .filter(
                Submittal.company_id == self.company_id,
                Submittal.sequence_name.isnot(None),
            )
            .order_by(Submittal.id.desc())
            .first()
        )
        num = 1
        if last and last[0]:
            match = re.search(r'(\d+)$', last[0])
            if match:
                num = int(match.group(1)) + 1
        return f"SUB{num:05d}"

    # ------------------------------------------------------------------
    # Submittal CRUD
    # ------------------------------------------------------------------

    def list_submittals(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """List submittals with pagination and filtering."""
        page_size = min(page_size, 200)
        query = self.db.query(Submittal).filter(
            Submittal.company_id == self.company_id,
        )

        if project_id:
            query = query.filter(Submittal.project_id == project_id)
        if status:
            query = query.filter(Submittal.status == status)
        if priority:
            query = query.filter(Submittal.priority == priority)
        if search:
            term = f"%{search}%"
            query = query.filter(
                (Submittal.title.ilike(term))
                | (Submittal.sequence_name.ilike(term))
                | (Submittal.spec_section.ilike(term))
            )

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(Submittal.id.desc()).offset(skip).limit(page_size).all()

        # Enrich with package/type names
        results = []
        for item in items:
            row = {c.key: getattr(item, c.key) for c in item.__table__.columns}
            row["package_name"] = item.package.name if item.package else None
            row["type_name"] = item.type_.name if item.type_ else None
            results.append(row)

        return {
            "items": results,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_submittal(self, submittal_id: int) -> Optional[Submittal]:
        """Get a single submittal by ID."""
        return (
            self.db.query(Submittal)
            .filter(
                Submittal.id == submittal_id,
                Submittal.company_id == self.company_id,
            )
            .first()
        )

    def get_submittal_detail(self, submittal_id: int) -> Optional[dict]:
        """Get submittal with approvers and labels."""
        submittal = self.get_submittal(submittal_id)
        if not submittal:
            return None

        row = {c.key: getattr(submittal, c.key) for c in submittal.__table__.columns}
        row["package_name"] = submittal.package.name if submittal.package else None
        row["type_name"] = submittal.type_.name if submittal.type_ else None
        row["label_ids"] = [lbl.id for lbl in submittal.labels]
        row["labels"] = [
            {"id": lbl.id, "name": lbl.name, "color": lbl.color}
            for lbl in submittal.labels
        ]
        row["approvers"] = [
            {
                "id": a.id,
                "user_id": a.user_id,
                "sequence": a.sequence,
                "status": a.status.value if hasattr(a.status, "value") else a.status,
                "comments": a.comments,
                "signed_at": a.signed_at,
                "user_name": (a.user.full_name or a.user.username or a.user.email) if a.user else None,
            }
            for a in submittal.approvers
        ]

        return row

    def create_submittal(self, data: SubmittalCreate) -> Submittal:
        """Create a new submittal with optional approvers and labels."""
        submittal = Submittal(
            company_id=self.company_id,
            sequence_name=self._next_sequence(),
            title=data.title,
            description=data.description,
            spec_section=data.spec_section,
            project_id=data.project_id,
            package_id=data.package_id,
            type_id=data.type_id,
            priority=data.priority or "medium",
            status="draft",
            due_date=data.due_date,
            submitted_date=data.submitted_date,
            received_date=data.received_date,
            submitted_by=self.user_id,
            created_by=self.user_id,
        )
        self.db.add(submittal)
        self.db.flush()

        # Add approvers
        if data.approver_ids:
            for ap in data.approver_ids:
                approver = SubmittalApprover(
                    submittal_id=submittal.id,
                    user_id=ap.user_id,
                    sequence=ap.sequence,
                    status=ApproverStatus.PENDING,
                    company_id=self.company_id,
                )
                self.db.add(approver)

        # Sync labels
        if data.label_ids:
            self._sync_labels(submittal.id, set(data.label_ids))

        self.db.commit()
        self.db.refresh(submittal)
        return submittal

    def update_submittal(self, submittal_id: int, data: SubmittalUpdate) -> Optional[Submittal]:
        """Update a submittal with partial data."""
        submittal = self.get_submittal(submittal_id)
        if not submittal:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Handle related fields separately
        label_ids = update_data.pop("label_ids", None)
        approver_ids = update_data.pop("approver_ids", None)

        for key, value in update_data.items():
            setattr(submittal, key, value)

        submittal.updated_by = self.user_id

        if label_ids is not None:
            self._sync_labels(submittal.id, set(label_ids))

        if approver_ids is not None:
            self._sync_approvers(submittal.id, approver_ids)

        self.db.commit()
        self.db.refresh(submittal)
        return submittal

    def delete_submittal(self, submittal_id: int) -> bool:
        """Hard-delete a submittal."""
        submittal = self.get_submittal(submittal_id)
        if not submittal:
            return False
        self.db.delete(submittal)
        self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Approval workflow
    # ------------------------------------------------------------------

    def approve_submittal(self, submittal_id: int, action: str, comments: Optional[str] = None) -> Optional[dict]:
        """
        Process an approval action by the current user.

        action: approve, approved_as_noted, reject, revise_and_submit
        """
        submittal = self.get_submittal(submittal_id)
        if not submittal:
            return None

        # Find this user's approver entry
        approver = (
            self.db.query(SubmittalApprover)
            .filter(
                SubmittalApprover.submittal_id == submittal_id,
                SubmittalApprover.user_id == self.user_id,
                SubmittalApprover.company_id == self.company_id,
            )
            .first()
        )
        if not approver:
            return {"error": "You are not an approver for this submittal"}

        # Map action to status
        action_map = {
            "approve": ApproverStatus.APPROVED,
            "approved_as_noted": ApproverStatus.APPROVED_AS_NOTED,
            "reject": ApproverStatus.REJECTED,
            "revise_and_submit": ApproverStatus.REVISE_AND_SUBMIT,
        }
        new_status = action_map.get(action)
        if not new_status:
            return {"error": f"Invalid action: {action}"}

        approver.status = new_status
        approver.comments = comments
        approver.signed_at = datetime.utcnow()

        # Update overall submittal status based on all approvers
        self._update_submittal_status(submittal)

        self.db.commit()
        self.db.refresh(submittal)
        return self.get_submittal_detail(submittal_id)

    def _update_submittal_status(self, submittal: Submittal):
        """Derive overall submittal status from approver statuses."""
        approvers = (
            self.db.query(SubmittalApprover)
            .filter(SubmittalApprover.submittal_id == submittal.id)
            .all()
        )
        if not approvers:
            return

        statuses = [a.status for a in approvers]

        # If any rejected => rejected
        if ApproverStatus.REJECTED in statuses:
            submittal.status = SubmittalStatus.REJECTED
        # If any revise_and_submit => rejected (needs resubmit)
        elif ApproverStatus.REVISE_AND_SUBMIT in statuses:
            submittal.status = SubmittalStatus.REJECTED
        # If all approved or approved_as_noted
        elif all(s in (ApproverStatus.APPROVED, ApproverStatus.APPROVED_AS_NOTED) for s in statuses):
            if ApproverStatus.APPROVED_AS_NOTED in statuses:
                submittal.status = SubmittalStatus.APPROVED_WITH_COMMENTS
            else:
                submittal.status = SubmittalStatus.APPROVED
        # Otherwise still in review
        else:
            submittal.status = SubmittalStatus.IN_REVIEW

    def resubmit_submittal(self, submittal_id: int) -> Optional[dict]:
        """Resubmit a rejected submittal: increment revision and reset approvers."""
        submittal = self.get_submittal(submittal_id)
        if not submittal:
            return None

        submittal.revision += 1
        submittal.status = SubmittalStatus.RESUBMITTED

        # Reset all approver statuses
        approvers = (
            self.db.query(SubmittalApprover)
            .filter(SubmittalApprover.submittal_id == submittal_id)
            .all()
        )
        for a in approvers:
            a.status = ApproverStatus.PENDING
            a.comments = None
            a.signed_at = None

        self.db.commit()
        self.db.refresh(submittal)
        return self.get_submittal_detail(submittal_id)

    # ------------------------------------------------------------------
    # M2M helpers
    # ------------------------------------------------------------------

    def _sync_labels(self, submittal_id: int, label_ids: set):
        """Sync submittal <-> labels M2M relationship."""
        self.db.execute(
            agcm_submittal_label_rel.delete().where(
                agcm_submittal_label_rel.c.submittal_id == submittal_id
            )
        )
        for lid in label_ids:
            self.db.execute(
                agcm_submittal_label_rel.insert().values(
                    submittal_id=submittal_id, label_id=lid
                )
            )

    def _sync_approvers(self, submittal_id: int, approver_data: list):
        """Replace approver chain for a submittal."""
        self.db.query(SubmittalApprover).filter(
            SubmittalApprover.submittal_id == submittal_id
        ).delete()
        for ap in approver_data:
            approver = SubmittalApprover(
                submittal_id=submittal_id,
                user_id=ap.user_id,
                sequence=ap.sequence,
                status=ApproverStatus.PENDING,
                company_id=self.company_id,
            )
            self.db.add(approver)

    # ------------------------------------------------------------------
    # Packages CRUD
    # ------------------------------------------------------------------

    def list_packages(self, project_id: Optional[int] = None) -> list:
        query = self.db.query(SubmittalPackage).filter(
            SubmittalPackage.company_id == self.company_id,
        )
        if project_id:
            query = query.filter(SubmittalPackage.project_id == project_id)
        return query.order_by(SubmittalPackage.name).all()

    def create_package(self, data: SubmittalPackageCreate) -> SubmittalPackage:
        pkg = SubmittalPackage(
            name=data.name,
            description=data.description,
            project_id=data.project_id,
            company_id=self.company_id,
        )
        self.db.add(pkg)
        self.db.commit()
        self.db.refresh(pkg)
        return pkg

    def delete_package(self, package_id: int) -> bool:
        pkg = (
            self.db.query(SubmittalPackage)
            .filter(
                SubmittalPackage.id == package_id,
                SubmittalPackage.company_id == self.company_id,
            )
            .first()
        )
        if not pkg:
            return False
        self.db.delete(pkg)
        self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Types CRUD
    # ------------------------------------------------------------------

    def list_types(self) -> list:
        return (
            self.db.query(SubmittalType)
            .filter(SubmittalType.company_id == self.company_id)
            .order_by(SubmittalType.name)
            .all()
        )

    def create_type(self, data: SubmittalTypeCreate) -> SubmittalType:
        obj = SubmittalType(name=data.name, company_id=self.company_id)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update_type(self, type_id: int, data: SubmittalTypeCreate):
        obj = (
            self.db.query(SubmittalType)
            .filter(
                SubmittalType.id == type_id,
                SubmittalType.company_id == self.company_id,
            )
            .first()
        )
        if not obj:
            return None
        obj.name = data.name
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_type(self, type_id: int) -> bool:
        obj = (
            self.db.query(SubmittalType)
            .filter(
                SubmittalType.id == type_id,
                SubmittalType.company_id == self.company_id,
            )
            .first()
        )
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Labels CRUD
    # ------------------------------------------------------------------

    def list_labels(self) -> list:
        return (
            self.db.query(SubmittalLabel)
            .filter(SubmittalLabel.company_id == self.company_id)
            .order_by(SubmittalLabel.name)
            .all()
        )

    def create_label(self, data: SubmittalLabelCreate) -> SubmittalLabel:
        obj = SubmittalLabel(
            name=data.name,
            color=data.color,
            company_id=self.company_id,
        )
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_label(self, label_id: int) -> bool:
        obj = (
            self.db.query(SubmittalLabel)
            .filter(
                SubmittalLabel.id == label_id,
                SubmittalLabel.company_id == self.company_id,
            )
            .first()
        )
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True
