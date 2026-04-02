"""Progress service for milestones, issues, estimation, s-curve, and project images"""

import logging
import re
from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from addons.agcm_progress.models.milestone import Milestone
from addons.agcm_progress.models.issue import Issue, IssueStatus
from addons.agcm_progress.models.estimation import EstimationItem
from addons.agcm_progress.models.scurve import SCurveData
from addons.agcm_progress.models.project_image import ProjectImage

try:
    from app.core.cache import cache

    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

try:
    from app.models.base import ActivityAction

    ACTIVITY_LOGGING_AVAILABLE = True
except ImportError:
    ACTIVITY_LOGGING_AVAILABLE = False

logger = logging.getLogger(__name__)

# Sequence configuration: tablename -> (prefix, padding)
SEQUENCE_CONFIG = {
    "agcm_milestones": ("MS", 5),
    "agcm_issues": ("ISS", 5),
    "agcm_project_images": ("IMG", 5),
}


class ProgressService:
    """Service for all progress-related CRUD operations."""

    def __init__(self, db: Session, company_id: int, user_id: int):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id

    def _invalidate_progress_cache(self, project_id: int = None):
        """Invalidate progress-related cache."""
        if not CACHE_AVAILABLE:
            return

        if project_id:
            cache.invalidate_pattern_distributed(
                f"agcm_progress:project:{self.company_id}:{project_id}:*"
            )
        cache.invalidate_pattern_distributed(f"agcm_progress:*")

    # -------------------------------------------------------------------------
    # Sequence generation
    # -------------------------------------------------------------------------
    def _next_sequence(self, model_class) -> Optional[str]:
        tablename = model_class.__tablename__
        config = SEQUENCE_CONFIG.get(tablename)
        if not config:
            return None

        prefix, padding = config
        last = (
            self.db.query(model_class.sequence_name)
            .filter(model_class.company_id == self.company_id)
            .filter(model_class.sequence_name.isnot(None))
            .order_by(model_class.id.desc())
            .first()
        )

        num = 1
        if last and last[0]:
            match = re.search(r"(\d+)$", last[0])
            if match:
                num = int(match.group(1)) + 1

        return f"{prefix}{num:0{padding}d}"

    # =========================================================================
    # MILESTONES
    # =========================================================================

    def list_milestones(self, project_id: int) -> List[Dict[str, Any]]:
        items = (
            self.db.query(Milestone)
            .filter(
                Milestone.project_id == project_id,
                Milestone.company_id == self.company_id,
            )
            .order_by(Milestone.planned_date.asc().nullslast(), Milestone.id.asc())
            .all()
        )
        return [self._milestone_to_dict(m) for m in items]

    def create_milestone(self, data) -> Milestone:
        milestone = Milestone(
            company_id=self.company_id,
            sequence_name=self._next_sequence(Milestone),
            name=data.name,
            description=data.description,
            planned_date=data.planned_date,
            actual_date=data.actual_date,
            is_completed=data.is_completed,
            project_id=data.project_id,
            created_by=self.user_id,
        )
        self.db.add(milestone)
        self.db.commit()
        self.db.refresh(milestone)
        self._invalidate_progress_cache(data.project_id)
        return milestone

    def update_milestone(self, milestone_id: int, data) -> Optional[Milestone]:
        milestone = (
            self.db.query(Milestone)
            .filter(
                Milestone.id == milestone_id, Milestone.company_id == self.company_id
            )
            .first()
        )
        if not milestone:
            return None

        project_id = milestone.project_id
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(milestone, key, value)
        milestone.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(milestone)
        self._invalidate_progress_cache(project_id)
        return milestone

    def delete_milestone(self, milestone_id: int) -> bool:
        milestone = (
            self.db.query(Milestone)
            .filter(
                Milestone.id == milestone_id, Milestone.company_id == self.company_id
            )
            .first()
        )
        if not milestone:
            return False
        project_id = milestone.project_id
        self.db.delete(milestone)
        self.db.commit()
        self._invalidate_progress_cache(project_id)
        return True

    def toggle_completed(self, milestone_id: int) -> Optional[Milestone]:
        milestone = (
            self.db.query(Milestone)
            .filter(
                Milestone.id == milestone_id, Milestone.company_id == self.company_id
            )
            .first()
        )
        if not milestone:
            return None

        project_id = milestone.project_id
        milestone.is_completed = not milestone.is_completed
        if milestone.is_completed and not milestone.actual_date:
            milestone.actual_date = date.today()
        milestone.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(milestone)
        self._invalidate_progress_cache(project_id)
        return milestone

    def _milestone_to_dict(self, m: Milestone) -> Dict[str, Any]:
        return {
            "id": m.id,
            "company_id": m.company_id,
            "sequence_name": m.sequence_name,
            "name": m.name,
            "description": m.description,
            "planned_date": str(m.planned_date) if m.planned_date else None,
            "actual_date": str(m.actual_date) if m.actual_date else None,
            "is_completed": m.is_completed,
            "project_id": m.project_id,
            "created_at": str(m.created_at) if m.created_at else None,
            "updated_at": str(m.updated_at) if m.updated_at else None,
        }

    # =========================================================================
    # ISSUES
    # =========================================================================

    def list_issues(
        self,
        project_id: int,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        query = self.db.query(Issue).filter(
            Issue.project_id == project_id, Issue.company_id == self.company_id
        )

        if status:
            query = query.filter(Issue.status == status)
        if severity:
            query = query.filter(Issue.severity == severity)
        if priority:
            query = query.filter(Issue.priority == priority)
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (Issue.title.ilike(search_filter))
                | (Issue.sequence_name.ilike(search_filter))
                | (Issue.location.ilike(search_filter))
            )

        total = query.count()
        items = (
            query.order_by(Issue.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "items": [self._issue_to_dict(i) for i in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_issue(self, issue_id: int) -> Optional[Dict[str, Any]]:
        issue = (
            self.db.query(Issue)
            .filter(Issue.id == issue_id, Issue.company_id == self.company_id)
            .first()
        )
        if not issue:
            return None
        return self._issue_to_dict(issue)

    def create_issue(self, data) -> Issue:
        issue = Issue(
            company_id=self.company_id,
            sequence_name=self._next_sequence(Issue),
            title=data.title,
            description=data.description,
            severity=data.severity,
            status=data.status,
            priority=data.priority,
            location=data.location,
            due_date=data.due_date,
            assigned_to=data.assigned_to,
            reported_by=data.reported_by or self.user_id,
            project_id=data.project_id,
            created_by=self.user_id,
        )
        self.db.add(issue)
        self.db.commit()
        self.db.refresh(issue)
        self._invalidate_progress_cache(data.project_id)
        return issue

    def update_issue(self, issue_id: int, data) -> Optional[Issue]:
        issue = (
            self.db.query(Issue)
            .filter(Issue.id == issue_id, Issue.company_id == self.company_id)
            .first()
        )
        if not issue:
            return None

        project_id = issue.project_id
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(issue, key, value)
        issue.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(issue)
        self._invalidate_progress_cache(project_id)
        return issue

    def delete_issue(self, issue_id: int) -> bool:
        issue = (
            self.db.query(Issue)
            .filter(Issue.id == issue_id, Issue.company_id == self.company_id)
            .first()
        )
        if not issue:
            return False
        project_id = issue.project_id
        self.db.delete(issue)
        self.db.commit()
        self._invalidate_progress_cache(project_id)
        return True

    def resolve_issue(self, issue_id: int) -> Optional[Issue]:
        issue = (
            self.db.query(Issue)
            .filter(Issue.id == issue_id, Issue.company_id == self.company_id)
            .first()
        )
        if not issue:
            return None

        project_id = issue.project_id
        issue.status = IssueStatus.RESOLVED
        issue.resolved_date = date.today()
        issue.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(issue)
        self._invalidate_progress_cache(project_id)
        return issue

    def close_issue(self, issue_id: int) -> Optional[Issue]:
        issue = (
            self.db.query(Issue)
            .filter(Issue.id == issue_id, Issue.company_id == self.company_id)
            .first()
        )
        if not issue:
            return None

        project_id = issue.project_id
        issue.status = IssueStatus.CLOSED
        if not issue.resolved_date:
            issue.resolved_date = date.today()
        issue.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(issue)
        self._invalidate_progress_cache(project_id)
        return issue

    def _issue_to_dict(self, i: Issue) -> Dict[str, Any]:
        return {
            "id": i.id,
            "company_id": i.company_id,
            "sequence_name": i.sequence_name,
            "title": i.title,
            "description": i.description,
            "severity": i.severity.value if i.severity else None,
            "status": i.status.value if i.status else None,
            "priority": i.priority.value if i.priority else None,
            "location": i.location,
            "due_date": str(i.due_date) if i.due_date else None,
            "resolved_date": str(i.resolved_date) if i.resolved_date else None,
            "assigned_to": i.assigned_to,
            "reported_by": i.reported_by,
            "project_id": i.project_id,
            "created_at": str(i.created_at) if i.created_at else None,
            "updated_at": str(i.updated_at) if i.updated_at else None,
        }

    # =========================================================================
    # ESTIMATION
    # =========================================================================

    def get_estimation_tree(self, project_id: int) -> List[Dict[str, Any]]:
        """Get hierarchical estimation items with rollup totals."""
        items = (
            self.db.query(EstimationItem)
            .filter(
                EstimationItem.project_id == project_id,
                EstimationItem.company_id == self.company_id,
            )
            .order_by(EstimationItem.id.asc())
            .all()
        )

        # Build lookup
        by_id = {}
        for item in items:
            by_id[item.id] = self._estimation_to_dict(item)
            by_id[item.id]["children"] = []
            by_id[item.id]["rollup_total"] = item.total_cost

        # Build tree
        roots = []
        for item in items:
            d = by_id[item.id]
            if item.parent_id and item.parent_id in by_id:
                by_id[item.parent_id]["children"].append(d)
            else:
                roots.append(d)

        # Calculate rollup totals bottom-up
        def calc_rollup(node):
            if not node["children"]:
                node["rollup_total"] = node["total_cost"]
                return node["rollup_total"]
            total = 0
            for child in node["children"]:
                total += calc_rollup(child)
            node["rollup_total"] = total
            return total

        for root in roots:
            calc_rollup(root)

        return roots

    def create_estimation_item(self, data) -> EstimationItem:
        # Auto-calculate total_cost if not explicitly set
        total_cost = data.total_cost
        if total_cost == 0 and data.quantity > 0 and data.unit_cost > 0:
            total_cost = data.quantity * data.unit_cost

        item = EstimationItem(
            company_id=self.company_id,
            name=data.name,
            description=data.description,
            cost_type=data.cost_type,
            quantity=data.quantity,
            unit=data.unit,
            unit_cost=data.unit_cost,
            total_cost=total_cost,
            status=data.status,
            parent_id=data.parent_id,
            project_id=data.project_id,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        self._invalidate_progress_cache(data.project_id)
        return item

    def update_estimation_item(self, item_id: int, data) -> Optional[EstimationItem]:
        item = (
            self.db.query(EstimationItem)
            .filter(
                EstimationItem.id == item_id,
                EstimationItem.company_id == self.company_id,
            )
            .first()
        )
        if not item:
            return None

        project_id = item.project_id
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)

        # Recalculate total if quantity or unit_cost changed
        if "quantity" in update_data or "unit_cost" in update_data:
            if item.quantity > 0 and item.unit_cost > 0:
                item.total_cost = item.quantity * item.unit_cost

        self.db.commit()
        self.db.refresh(item)
        self._invalidate_progress_cache(project_id)
        return item

    def delete_estimation_item(self, item_id: int) -> bool:
        item = (
            self.db.query(EstimationItem)
            .filter(
                EstimationItem.id == item_id,
                EstimationItem.company_id == self.company_id,
            )
            .first()
        )
        if not item:
            return False
        project_id = item.project_id
        self.db.delete(item)
        self.db.commit()
        self._invalidate_progress_cache(project_id)
        return True

    def _estimation_to_dict(self, e: EstimationItem) -> Dict[str, Any]:
        return {
            "id": e.id,
            "company_id": e.company_id,
            "name": e.name,
            "description": e.description,
            "cost_type": e.cost_type.value if e.cost_type else None,
            "quantity": e.quantity,
            "unit": e.unit,
            "unit_cost": e.unit_cost,
            "total_cost": e.total_cost,
            "status": e.status.value if e.status else None,
            "parent_id": e.parent_id,
            "project_id": e.project_id,
            "created_at": str(e.created_at) if e.created_at else None,
            "updated_at": str(e.updated_at) if e.updated_at else None,
        }

    # =========================================================================
    # S-CURVE
    # =========================================================================

    def get_scurve_chart_data(self, project_id: int) -> List[Dict[str, Any]]:
        items = (
            self.db.query(SCurveData)
            .filter(
                SCurveData.project_id == project_id,
                SCurveData.company_id == self.company_id,
            )
            .order_by(SCurveData.date.asc())
            .all()
        )
        return [self._scurve_to_dict(s) for s in items]

    def create_scurve_data(self, data) -> SCurveData:
        scurve = SCurveData(
            company_id=self.company_id,
            project_id=data.project_id,
            date=data.date,
            planned_physical_pct=data.planned_physical_pct,
            actual_physical_pct=data.actual_physical_pct,
            revised_physical_pct=data.revised_physical_pct,
            planned_financial_pct=data.planned_financial_pct,
            actual_financial_pct=data.actual_financial_pct,
            manpower_progress_pct=data.manpower_progress_pct,
            machinery_progress_pct=data.machinery_progress_pct,
            schedule_days_ahead=data.schedule_days_ahead,
        )
        self.db.add(scurve)
        self.db.commit()
        self.db.refresh(scurve)
        self._invalidate_progress_cache(data.project_id)
        return scurve

    def update_scurve_data(self, scurve_id: int, data) -> Optional[SCurveData]:
        scurve = (
            self.db.query(SCurveData)
            .filter(
                SCurveData.id == scurve_id, SCurveData.company_id == self.company_id
            )
            .first()
        )
        if not scurve:
            return None

        project_id = scurve.project_id
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(scurve, key, value)

        self.db.commit()
        self.db.refresh(scurve)
        self._invalidate_progress_cache(project_id)
        return scurve

    def delete_scurve_data(self, scurve_id: int) -> bool:
        scurve = (
            self.db.query(SCurveData)
            .filter(
                SCurveData.id == scurve_id, SCurveData.company_id == self.company_id
            )
            .first()
        )
        if not scurve:
            return False
        project_id = scurve.project_id
        self.db.delete(scurve)
        self.db.commit()
        self._invalidate_progress_cache(project_id)
        return True

    def _scurve_to_dict(self, s: SCurveData) -> Dict[str, Any]:
        return {
            "id": s.id,
            "company_id": s.company_id,
            "project_id": s.project_id,
            "date": str(s.date) if s.date else None,
            "planned_physical_pct": s.planned_physical_pct,
            "actual_physical_pct": s.actual_physical_pct,
            "revised_physical_pct": s.revised_physical_pct,
            "planned_financial_pct": s.planned_financial_pct,
            "actual_financial_pct": s.actual_financial_pct,
            "manpower_progress_pct": s.manpower_progress_pct,
            "machinery_progress_pct": s.machinery_progress_pct,
            "schedule_days_ahead": s.schedule_days_ahead,
            "created_at": str(s.created_at) if s.created_at else None,
            "updated_at": str(s.updated_at) if s.updated_at else None,
        }

    # =========================================================================
    # PROJECT IMAGES
    # =========================================================================

    def list_project_images(self, project_id: int) -> List[Dict[str, Any]]:
        items = (
            self.db.query(ProjectImage)
            .filter(
                ProjectImage.project_id == project_id,
                ProjectImage.company_id == self.company_id,
            )
            .order_by(ProjectImage.display_order.asc(), ProjectImage.id.desc())
            .all()
        )
        return [self._image_to_dict(img) for img in items]

    def create_project_image(
        self,
        project_id: int,
        name: str,
        file_name: Optional[str] = None,
        file_url: Optional[str] = None,
        document_id: Optional[int] = None,
        description: Optional[str] = None,
        tags: Optional[str] = None,
        taken_on: Optional[date] = None,
        display_order: int = 0,
    ) -> ProjectImage:
        img = ProjectImage(
            company_id=self.company_id,
            sequence_name=self._next_sequence(ProjectImage),
            name=name,
            description=description,
            tags=tags,
            document_id=document_id,
            file_url=file_url,
            file_name=file_name,
            display_order=display_order,
            taken_on=taken_on,
            project_id=project_id,
            created_by=self.user_id,
        )
        self.db.add(img)
        self.db.commit()
        self.db.refresh(img)
        self._invalidate_progress_cache(project_id)
        return img

    def update_project_image(self, image_id: int, data) -> Optional[ProjectImage]:
        img = (
            self.db.query(ProjectImage)
            .filter(
                ProjectImage.id == image_id, ProjectImage.company_id == self.company_id
            )
            .first()
        )
        if not img:
            return None

        project_id = img.project_id
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(img, key, value)
        img.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(img)
        self._invalidate_progress_cache(project_id)
        return img

    def delete_project_image(self, image_id: int) -> bool:
        img = (
            self.db.query(ProjectImage)
            .filter(
                ProjectImage.id == image_id, ProjectImage.company_id == self.company_id
            )
            .first()
        )
        if not img:
            return False
        project_id = img.project_id
        self.db.delete(img)
        self.db.commit()
        self._invalidate_progress_cache(project_id)
        return True

    def _image_to_dict(self, img: ProjectImage) -> Dict[str, Any]:
        return {
            "id": img.id,
            "company_id": img.company_id,
            "sequence_name": img.sequence_name,
            "name": img.name,
            "description": img.description,
            "tags": img.tags,
            "document_id": img.document_id,
            "file_url": img.file_url,
            "file_name": img.file_name,
            "display_order": img.display_order,
            "taken_on": str(img.taken_on) if img.taken_on else None,
            "project_id": img.project_id,
            "created_at": str(img.created_at) if img.created_at else None,
            "updated_at": str(img.updated_at) if img.updated_at else None,
        }
