"""Portal service - business logic for selections, bids, and portal config"""

import logging
from datetime import date
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from addons.agcm_portal.models.selection import Selection, SelectionOption, SelectionStatus
from addons.agcm_portal.models.bid import BidPackage, BidSubmission, BidStatus
from addons.agcm_portal.models.portal_config import PortalConfig
from addons.agcm_portal.schemas.selection import (
    SelectionCreate, SelectionUpdate,
    SelectionOptionCreate, SelectionOptionUpdate,
)
from addons.agcm_portal.schemas.bid import (
    BidPackageCreate, BidPackageUpdate,
    BidSubmissionCreate, BidSubmissionUpdate,
)
from addons.agcm_portal.schemas.portal_config import PortalConfigCreate, PortalConfigUpdate

logger = logging.getLogger(__name__)

# Sequence config for bid packages
SEQUENCE_CONFIG = {
    "agcm_bid_packages": ("BID", 5),
}


def _next_bid_sequence(db: Session, company_id: int) -> str:
    """Generate next bid package sequence: BID00001, BID00002, etc."""
    import re
    prefix, padding = SEQUENCE_CONFIG["agcm_bid_packages"]
    last = (
        db.query(BidPackage.sequence_name)
        .filter(BidPackage.company_id == company_id)
        .filter(BidPackage.sequence_name.isnot(None))
        .order_by(BidPackage.id.desc())
        .first()
    )
    num = 1
    if last and last[0]:
        match = re.search(r'(\d+)$', last[0])
        if match:
            num = int(match.group(1)) + 1
    return f"{prefix}{num:0{padding}d}"


class PortalService:
    """Handles portal CRUD and business logic for selections, bids, and config."""

    def __init__(self, db: Session, company_id: int, user_id: int):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id

    # =========================================================================
    # SELECTIONS
    # =========================================================================

    def list_selections(
        self,
        page: int = 1,
        page_size: int = 20,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict:
        """List selections with pagination and filtering."""
        page_size = min(page_size, 200)
        query = (
            self.db.query(Selection)
            .options(joinedload(Selection.options))
            .filter(Selection.company_id == self.company_id)
        )

        if project_id:
            query = query.filter(Selection.project_id == project_id)
        if status:
            query = query.filter(Selection.status == status)
        if category:
            query = query.filter(Selection.category == category)
        if search:
            term = f"%{search}%"
            query = query.filter(
                (Selection.name.ilike(term)) | (Selection.description.ilike(term))
            )

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(Selection.id.desc()).offset(skip).limit(page_size).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_selection(self, selection_id: int) -> Optional[Selection]:
        """Get a single selection by ID."""
        return (
            self.db.query(Selection)
            .options(joinedload(Selection.options))
            .filter(
                Selection.id == selection_id,
                Selection.company_id == self.company_id,
            )
            .first()
        )

    def create_selection(self, data: SelectionCreate) -> Selection:
        """Create a selection with optional inline options."""
        selection = Selection(
            company_id=self.company_id,
            project_id=data.project_id,
            name=data.name,
            category=data.category,
            description=data.description,
            location=data.location,
            status="pending",
            due_date=data.due_date,
            budget_amount=data.budget_amount,
            notes=data.notes,
            created_by=self.user_id,
        )
        self.db.add(selection)
        self.db.flush()

        for opt_data in (data.options or []):
            option = SelectionOption(
                selection_id=selection.id,
                company_id=self.company_id,
                name=opt_data.name,
                description=opt_data.description,
                price=opt_data.price,
                unit=opt_data.unit,
                image_url=opt_data.image_url,
                spec_url=opt_data.spec_url,
                is_recommended=opt_data.is_recommended,
                is_selected=opt_data.is_selected,
                display_order=opt_data.display_order,
            )
            self.db.add(option)

        self.db.commit()
        self.db.refresh(selection)
        return selection

    def update_selection(self, selection_id: int, data: SelectionUpdate) -> Optional[Selection]:
        """Update a selection with partial data."""
        selection = self.get_selection(selection_id)
        if not selection:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(selection, key, value)
        selection.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(selection)
        return selection

    def delete_selection(self, selection_id: int) -> bool:
        """Delete a selection and its options."""
        selection = self.get_selection(selection_id)
        if not selection:
            return False
        self.db.delete(selection)
        self.db.commit()
        return True

    def approve_selection(self, selection_id: int, option_id: int, decided_by: str = None) -> Optional[Selection]:
        """Approve a selection by choosing an option, updating budget impact."""
        selection = self.get_selection(selection_id)
        if not selection:
            return None

        # Clear previous selections
        for opt in selection.options:
            opt.is_selected = False

        # Find and select the chosen option
        chosen = self.db.query(SelectionOption).filter(
            SelectionOption.id == option_id,
            SelectionOption.selection_id == selection_id,
        ).first()
        if not chosen:
            return None

        chosen.is_selected = True
        selection.status = SelectionStatus.APPROVED.value
        selection.selected_amount = chosen.price
        selection.budget_impact = chosen.price - selection.budget_amount
        selection.decided_date = date.today()
        selection.decided_by = decided_by or str(self.user_id)
        selection.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(selection)
        return selection

    def reject_selection(self, selection_id: int) -> Optional[Selection]:
        """Reject a selection."""
        selection = self.get_selection(selection_id)
        if not selection:
            return None

        selection.status = SelectionStatus.REJECTED.value
        selection.decided_date = date.today()
        selection.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(selection)
        return selection

    # --- Selection Options ---

    def create_option(self, selection_id: int, data: SelectionOptionCreate) -> Optional[SelectionOption]:
        """Add an option to a selection."""
        selection = self.get_selection(selection_id)
        if not selection:
            return None

        option = SelectionOption(
            selection_id=selection_id,
            company_id=self.company_id,
            name=data.name,
            description=data.description,
            price=data.price,
            unit=data.unit,
            image_url=data.image_url,
            spec_url=data.spec_url,
            is_recommended=data.is_recommended,
            is_selected=data.is_selected,
            display_order=data.display_order,
        )
        self.db.add(option)
        self.db.commit()
        self.db.refresh(option)
        return option

    def update_option(self, option_id: int, data: SelectionOptionUpdate) -> Optional[SelectionOption]:
        """Update an option."""
        option = (
            self.db.query(SelectionOption)
            .filter(
                SelectionOption.id == option_id,
                SelectionOption.company_id == self.company_id,
            )
            .first()
        )
        if not option:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(option, key, value)

        self.db.commit()
        self.db.refresh(option)
        return option

    def delete_option(self, option_id: int) -> bool:
        """Delete an option."""
        option = (
            self.db.query(SelectionOption)
            .filter(
                SelectionOption.id == option_id,
                SelectionOption.company_id == self.company_id,
            )
            .first()
        )
        if not option:
            return False
        self.db.delete(option)
        self.db.commit()
        return True

    # =========================================================================
    # BID PACKAGES
    # =========================================================================

    def list_bid_packages(
        self,
        page: int = 1,
        page_size: int = 20,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict:
        """List bid packages with pagination."""
        page_size = min(page_size, 200)
        query = (
            self.db.query(BidPackage)
            .options(joinedload(BidPackage.submissions))
            .filter(BidPackage.company_id == self.company_id)
        )

        if project_id:
            query = query.filter(BidPackage.project_id == project_id)
        if status:
            query = query.filter(BidPackage.status == status)
        if search:
            term = f"%{search}%"
            query = query.filter(
                (BidPackage.name.ilike(term)) | (BidPackage.trade.ilike(term))
            )

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(BidPackage.id.desc()).offset(skip).limit(page_size).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_bid_package(self, bid_package_id: int) -> Optional[BidPackage]:
        """Get a single bid package by ID."""
        return (
            self.db.query(BidPackage)
            .options(joinedload(BidPackage.submissions))
            .filter(
                BidPackage.id == bid_package_id,
                BidPackage.company_id == self.company_id,
            )
            .first()
        )

    def create_bid_package(self, data: BidPackageCreate) -> BidPackage:
        """Create a bid package with auto-generated sequence."""
        bp = BidPackage(
            company_id=self.company_id,
            project_id=data.project_id,
            sequence_name=_next_bid_sequence(self.db, self.company_id),
            name=data.name,
            description=data.description,
            trade=data.trade,
            due_date=data.due_date,
            status="open",
            notes=data.notes,
            created_by=self.user_id,
        )
        self.db.add(bp)
        self.db.commit()
        self.db.refresh(bp)
        return bp

    def update_bid_package(self, bid_package_id: int, data: BidPackageUpdate) -> Optional[BidPackage]:
        """Update a bid package."""
        bp = self.get_bid_package(bid_package_id)
        if not bp:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(bp, key, value)
        bp.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(bp)
        return bp

    def delete_bid_package(self, bid_package_id: int) -> bool:
        """Delete a bid package and its submissions."""
        bp = self.get_bid_package(bid_package_id)
        if not bp:
            return False
        self.db.delete(bp)
        self.db.commit()
        return True

    # =========================================================================
    # BID SUBMISSIONS
    # =========================================================================

    def create_submission(self, bid_package_id: int, data: BidSubmissionCreate) -> Optional[BidSubmission]:
        """Add a submission to a bid package."""
        bp = self.get_bid_package(bid_package_id)
        if not bp:
            return None

        sub = BidSubmission(
            bid_package_id=bid_package_id,
            company_id=self.company_id,
            vendor_name=data.vendor_name,
            vendor_email=data.vendor_email,
            vendor_phone=data.vendor_phone,
            status="draft",
            total_amount=data.total_amount,
            scope_description=data.scope_description,
            exclusions=data.exclusions,
            submitted_date=data.submitted_date,
            document_url=data.document_url,
            notes=data.notes,
        )
        self.db.add(sub)
        self.db.commit()
        self.db.refresh(sub)
        return sub

    def update_submission(self, submission_id: int, data: BidSubmissionUpdate) -> Optional[BidSubmission]:
        """Update a bid submission."""
        sub = (
            self.db.query(BidSubmission)
            .filter(
                BidSubmission.id == submission_id,
                BidSubmission.company_id == self.company_id,
            )
            .first()
        )
        if not sub:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(sub, key, value)

        self.db.commit()
        self.db.refresh(sub)
        return sub

    def delete_submission(self, submission_id: int) -> bool:
        """Delete a bid submission."""
        sub = (
            self.db.query(BidSubmission)
            .filter(
                BidSubmission.id == submission_id,
                BidSubmission.company_id == self.company_id,
            )
            .first()
        )
        if not sub:
            return False
        self.db.delete(sub)
        self.db.commit()
        return True

    def award_bid(self, submission_id: int) -> Optional[BidSubmission]:
        """Award a bid to a submission, rejecting others in the same package."""
        sub = (
            self.db.query(BidSubmission)
            .filter(
                BidSubmission.id == submission_id,
                BidSubmission.company_id == self.company_id,
            )
            .first()
        )
        if not sub:
            return None

        # Reject all other submissions in this package
        self.db.query(BidSubmission).filter(
            BidSubmission.bid_package_id == sub.bid_package_id,
            BidSubmission.id != submission_id,
        ).update({"is_awarded": False, "status": BidStatus.REJECTED.value})

        sub.is_awarded = True
        sub.status = BidStatus.AWARDED.value

        # Mark package as awarded
        bp = self.get_bid_package(sub.bid_package_id)
        if bp:
            bp.status = "awarded"

        self.db.commit()
        self.db.refresh(sub)
        return sub

    # =========================================================================
    # PORTAL CONFIG
    # =========================================================================

    def get_portal_config(self, project_id: int) -> Optional[PortalConfig]:
        """Get portal config for a project."""
        return (
            self.db.query(PortalConfig)
            .filter(
                PortalConfig.project_id == project_id,
                PortalConfig.company_id == self.company_id,
            )
            .first()
        )

    def create_or_update_portal_config(self, data: PortalConfigCreate) -> PortalConfig:
        """Create or update portal config (upsert by project_id)."""
        existing = self.get_portal_config(data.project_id)
        if existing:
            update_data = data.model_dump(exclude={"project_id"})
            for key, value in update_data.items():
                setattr(existing, key, value)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        config = PortalConfig(
            company_id=self.company_id,
            project_id=data.project_id,
            client_portal_enabled=data.client_portal_enabled,
            sub_portal_enabled=data.sub_portal_enabled,
            show_budget=data.show_budget,
            show_schedule=data.show_schedule,
            show_documents=data.show_documents,
            show_photos=data.show_photos,
            show_daily_logs=data.show_daily_logs,
            welcome_message=data.welcome_message,
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def update_portal_config(self, config_id: int, data: PortalConfigUpdate) -> Optional[PortalConfig]:
        """Update a portal config."""
        config = (
            self.db.query(PortalConfig)
            .filter(
                PortalConfig.id == config_id,
                PortalConfig.company_id == self.company_id,
            )
            .first()
        )
        if not config:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(config, key, value)

        self.db.commit()
        self.db.refresh(config)
        return config

    def delete_portal_config(self, config_id: int) -> bool:
        """Delete a portal config."""
        config = (
            self.db.query(PortalConfig)
            .filter(
                PortalConfig.id == config_id,
                PortalConfig.company_id == self.company_id,
            )
            .first()
        )
        if not config:
            return False
        self.db.delete(config)
        self.db.commit()
        return True

    # =========================================================================
    # DASHBOARDS
    # =========================================================================

    def get_client_dashboard(self, project_id: int) -> dict:
        """Get client dashboard data for a project."""
        config = self.get_portal_config(project_id)

        # Selection summary
        sel_query = self.db.query(Selection).filter(
            Selection.project_id == project_id,
            Selection.company_id == self.company_id,
        )
        total_selections = sel_query.count()
        pending_selections = sel_query.filter(Selection.status == "pending").count()
        approved_selections = sel_query.filter(Selection.status == "approved").count()
        total_budget_impact = (
            self.db.query(func.coalesce(func.sum(Selection.budget_impact), 0))
            .filter(
                Selection.project_id == project_id,
                Selection.company_id == self.company_id,
                Selection.status == "approved",
            )
            .scalar()
        )

        return {
            "portal_config": config,
            "selections": {
                "total": total_selections,
                "pending": pending_selections,
                "approved": approved_selections,
                "total_budget_impact": float(total_budget_impact or 0),
            },
        }

    def get_sub_dashboard(self, project_id: int, vendor_name: Optional[str] = None) -> dict:
        """Get subcontractor dashboard data for a project."""
        bp_query = self.db.query(BidPackage).filter(
            BidPackage.project_id == project_id,
            BidPackage.company_id == self.company_id,
        )
        total_packages = bp_query.count()
        open_packages = bp_query.filter(BidPackage.status == "open").count()

        sub_query = self.db.query(BidSubmission).join(BidPackage).filter(
            BidPackage.project_id == project_id,
            BidSubmission.company_id == self.company_id,
        )
        if vendor_name:
            sub_query = sub_query.filter(BidSubmission.vendor_name == vendor_name)

        total_submissions = sub_query.count()
        awarded_submissions = sub_query.filter(BidSubmission.is_awarded == True).count()

        return {
            "bid_packages": {
                "total": total_packages,
                "open": open_packages,
            },
            "submissions": {
                "total": total_submissions,
                "awarded": awarded_submissions,
            },
        }
