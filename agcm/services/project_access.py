"""
Project-level access control helpers.

Provides reusable functions for filtering queries by project membership
and checking project-level roles.

Usage in any AGCM service:
    from addons.agcm.services.project_access import (
        get_user_project_ids, has_project_access, check_project_role
    )

    # Filter list query to user's projects
    project_ids = get_user_project_ids(db, user_id, company_id)
    query = query.filter(Model.project_id.in_(project_ids))

    # Check if user can access a specific project
    if not has_project_access(db, user_id, project_id):
        raise HTTPException(403, "No access to this project")

    # Check for minimum role
    if not check_project_role(db, user_id, project_id, min_role="manager"):
        raise HTTPException(403, "Manager role required")
"""

import logging
from typing import List, Optional, Set

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Role hierarchy (higher index = more permissions)
ROLE_HIERARCHY = ["viewer", "member", "manager", "owner"]


def _get_member_model():
    """Lazy-import ProjectMember."""
    import sys
    mod = sys.modules.get("agcm_project_member")
    if mod:
        return mod.ProjectMember
    from addons.agcm.models.project_member import ProjectMember
    return ProjectMember


def get_user_project_ids(
    db: Session,
    user_id: int,
    company_id: int,
    min_role: Optional[str] = None,
) -> List[int]:
    """
    Get project IDs the user has access to within a company.

    Args:
        db: Database session
        user_id: User to check
        company_id: Company scope
        min_role: Minimum role required (None = any membership)

    Returns:
        List of project_id values the user can access.
    """
    ProjectMember = _get_member_model()

    query = db.query(ProjectMember.project_id).filter(
        ProjectMember.user_id == user_id,
        ProjectMember.company_id == company_id,
        ProjectMember.is_active == True,
    )

    if min_role and min_role in ROLE_HIERARCHY:
        min_idx = ROLE_HIERARCHY.index(min_role)
        allowed_roles = ROLE_HIERARCHY[min_idx:]
        query = query.filter(ProjectMember.role.in_(allowed_roles))

    return [r[0] for r in query.all()]


def has_project_access(
    db: Session,
    user_id: int,
    project_id: int,
    min_role: Optional[str] = None,
) -> bool:
    """
    Check if a user has access to a specific project.

    Args:
        user_id: User to check
        project_id: Project to check access for
        min_role: Minimum role required (None = any membership)

    Returns:
        True if user has access, False otherwise.
    """
    ProjectMember = _get_member_model()

    query = db.query(ProjectMember.id).filter(
        ProjectMember.user_id == user_id,
        ProjectMember.project_id == project_id,
        ProjectMember.is_active == True,
    )

    if min_role and min_role in ROLE_HIERARCHY:
        min_idx = ROLE_HIERARCHY.index(min_role)
        allowed_roles = ROLE_HIERARCHY[min_idx:]
        query = query.filter(ProjectMember.role.in_(allowed_roles))

    return query.first() is not None


def get_project_role(
    db: Session,
    user_id: int,
    project_id: int,
) -> Optional[str]:
    """
    Get the user's role in a specific project.

    Returns:
        Role string ("owner", "manager", "member", "viewer") or None if not a member.
    """
    ProjectMember = _get_member_model()

    member = db.query(ProjectMember).filter(
        ProjectMember.user_id == user_id,
        ProjectMember.project_id == project_id,
        ProjectMember.is_active == True,
    ).first()

    return member.role if member else None


def check_project_role(
    db: Session,
    user_id: int,
    project_id: int,
    min_role: str = "viewer",
) -> bool:
    """
    Check if user has at least the specified role in a project.

    Returns:
        True if user's role is >= min_role in the hierarchy.
    """
    role = get_project_role(db, user_id, project_id)
    if not role:
        return False

    if role not in ROLE_HIERARCHY or min_role not in ROLE_HIERARCHY:
        return False

    return ROLE_HIERARCHY.index(role) >= ROLE_HIERARCHY.index(min_role)
