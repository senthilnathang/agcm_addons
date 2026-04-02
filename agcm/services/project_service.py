"""Project service - business logic for construction projects"""

import hashlib
import json
import logging
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from addons.agcm.models.project import (
    Project,
    agcm_project_users,
    agcm_project_contractors,
)
from addons.agcm.models.daily_activity_log import DailyActivityLog
from addons.agcm.schemas.project import ProjectCreate, ProjectUpdate
from addons.agcm.services.sequence_service import next_sequence

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


def _serialize_for_cache(obj):
    """Serialize ORM objects for cache storage."""
    if hasattr(obj, "__table__"):
        result = {}
        for col in obj.__table__.columns:
            val = getattr(obj, col.key, None)
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            elif hasattr(val, "tolist"):
                val = val.tolist()
            elif hasattr(val, "__iter__") and not isinstance(
                val, (str, bytes, dict, list)
            ):
                val = list(val)
            result[col.key] = val
        return result
    return obj


class ProjectService:
    """
    Handles Project CRUD and business logic.

    Migrated business rules from Odoo:
    - Auto-generates sequence_name (PROJ-XXXX)
    - Owner is auto-added to project users
    - Current user is auto-added to project users
    - Lat/lng auto-computed from ZIP + country on create/update
    - Non-management users only see assigned projects
    """

    def __init__(self, db: Session, company_id: int, user_id: int):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id

    def _next_sequence(self) -> str:
        """Generate next project sequence: Proj00001, Proj00002, etc."""
        return next_sequence(self.db, Project, self.company_id)

    def list_projects(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
        is_management: bool = True,
    ) -> dict:
        """
        List projects with pagination and filtering.

        Non-management users only see projects they are assigned to.
        """
        page_size = min(page_size, 200)
        query = self.db.query(Project).filter(
            Project.company_id == self.company_id,
            Project.is_deleted == False,
        )

        # Non-management: only assigned projects
        if not is_management:
            query = query.filter(Project.user_ids.any(id=self.user_id))

        if status:
            query = query.filter(Project.status == status)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Project.name.ilike(search_term))
                | (Project.ref_number.ilike(search_term))
                | (Project.sequence_name.ilike(search_term))
            )

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(Project.id.desc()).offset(skip).limit(page_size).all()

        return {
            "items": items,
            "results": items,
            "total": total,
            "count": total,
            "page": page,
            "page_size": page_size,
        }

    def get_project(self, project_id: int) -> Optional[Project]:
        """Get a single project by ID."""
        return (
            self.db.query(Project)
            .filter(
                Project.id == project_id,
                Project.company_id == self.company_id,
                Project.is_deleted == False,
            )
            .first()
        )

    def _get_project_detail_uncached(self, project_id: int) -> dict:
        """Internal method to get project detail without caching."""
        project = self.get_project(project_id)
        if not project:
            return None

        daily_log_count = (
            self.db.query(func.count(DailyActivityLog.id))
            .filter(DailyActivityLog.project_id == project_id)
            .scalar()
        )

        user_ids = [u.id for u in project.user_ids]
        partner_ids = [p.id for p in project.partner_ids]

        return {
            **_serialize_for_cache(project),
            "user_ids": user_ids,
            "partner_ids": partner_ids,
            "daily_log_count": daily_log_count or 0,
        }

    def get_project_detail(self, project_id: int) -> Optional[dict]:
        """Get project with related counts (cached)."""
        cache_key = f"agcm:project_detail:{self.company_id}:{project_id}"

        if CACHE_AVAILABLE:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        detail = self._get_project_detail_uncached(project_id)

        if detail and CACHE_AVAILABLE:
            cache.set(cache_key, detail, ttl=300)

        return detail

    def _invalidate_project_cache(self, project_id: int = None):
        """Invalidate project-related cache."""
        if not CACHE_AVAILABLE:
            return

        if project_id:
            cache.invalidate(f"agcm:project_detail:{self.company_id}:{project_id}")

        cache.invalidate_pattern_distributed(f"agcm:project_list:{self.company_id}:*")

    def create_project(self, data: ProjectCreate) -> Project:
        """
        Create a new project.

        Business rules:
        - Auto-generate sequence_name
        - Owner auto-added to user_ids
        - Current user auto-added to user_ids
        """
        project = Project(
            company_id=self.company_id,
            sequence_name=self._next_sequence(),
            name=data.name,
            ref_number=data.ref_number,
            start_date=data.start_date,
            end_date=data.end_date,
            status=data.status or "new",
            trade_id=data.trade_id,
            owner_id=data.owner_id,
            street=data.street,
            city=data.city,
            zip=data.zip,
            state=data.state,
            country=data.country,
            agcm_office=data.agcm_office,
            created_by=self.user_id,
        )

        self.db.add(project)
        self.db.flush()

        # Build user list: explicit + owner + current user
        user_set = set(data.user_ids or [])
        user_set.add(data.owner_id)
        user_set.add(self.user_id)
        self._sync_m2m_users(project.id, user_set)

        # Contractors
        if data.partner_ids:
            self._sync_m2m_partners(project.id, set(data.partner_ids))

        self.db.commit()
        self.db.refresh(project)

        self._invalidate_project_cache()

        if ACTIVITY_LOGGING_AVAILABLE:
            project.log_activity(
                self.db,
                ActivityAction.CREATE,
                user_id=self.user_id,
                description=f"Project '{project.name}' created",
                new_values={
                    "name": project.name,
                    "status": str(
                        project.status.value
                        if hasattr(project.status, "value")
                        else project.status
                    ),
                },
            )

        return project

    def update_project(self, project_id: int, data: ProjectUpdate) -> Optional[Project]:
        """Update a project with partial data."""
        project = self.get_project(project_id)
        if not project:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Handle M2M fields separately
        user_ids = update_data.pop("user_ids", None)
        partner_ids = update_data.pop("partner_ids", None)

        for key, value in update_data.items():
            setattr(project, key, value)

        project.updated_by = self.user_id

        if user_ids is not None:
            user_set = set(user_ids)
            # Ensure owner and current user stay in
            user_set.add(project.owner_id)
            user_set.add(self.user_id)
            self._sync_m2m_users(project.id, user_set)

        if partner_ids is not None:
            self._sync_m2m_partners(project.id, set(partner_ids))

        self.db.commit()
        self.db.refresh(project)

        self._invalidate_project_cache(project_id)

        if ACTIVITY_LOGGING_AVAILABLE:
            project.log_activity(
                self.db,
                ActivityAction.UPDATE,
                user_id=self.user_id,
                description=f"Project '{project.name}' updated",
            )

        return project

    def delete_project(self, project_id: int) -> bool:
        """Soft-delete a project."""
        project = self.get_project(project_id)
        if not project:
            return False
        project_name = project.name
        project.soft_delete(user_id=self.user_id)
        self.db.commit()
        self._invalidate_project_cache(project_id)

        if ACTIVITY_LOGGING_AVAILABLE:
            project.log_activity(
                self.db,
                ActivityAction.ARCHIVE,
                user_id=self.user_id,
                description=f"Project '{project_name}' archived",
            )

        return True

    # --- M2M helpers ---

    def _sync_m2m_users(self, project_id: int, user_ids: set):
        """Sync project <-> users M2M relationship."""
        self.db.execute(
            agcm_project_users.delete().where(
                agcm_project_users.c.project_id == project_id
            )
        )
        for uid in user_ids:
            self.db.execute(
                agcm_project_users.insert().values(project_id=project_id, user_id=uid)
            )

    def _sync_m2m_partners(self, project_id: int, partner_ids: set):
        """Sync project <-> contractors M2M relationship."""
        self.db.execute(
            agcm_project_contractors.delete().where(
                agcm_project_contractors.c.project_id == project_id
            )
        )
        for pid in partner_ids:
            self.db.execute(
                agcm_project_contractors.insert().values(
                    project_id=project_id, partner_id=pid
                )
            )
