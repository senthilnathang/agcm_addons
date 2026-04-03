"""API routes for project member management."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id

router = APIRouter()


class AddMemberRequest(BaseModel):
    user_id: int
    role: str = Field("member", description="owner, manager, member, or viewer")


class UpdateMemberRoleRequest(BaseModel):
    role: str = Field(..., description="owner, manager, member, or viewer")


class ProjectMemberResponse(BaseModel):
    id: int
    project_id: int
    user_id: int
    role: str
    is_active: bool
    assigned_at: Optional[str] = None
    assigned_by: Optional[int] = None


def _get_member_model():
    import sys
    mod = sys.modules.get("agcm_project_member")
    if mod:
        return mod.ProjectMember
    from addons.agcm.models.project_member import ProjectMember
    return ProjectMember


@router.get("/projects/{project_id}/members")
async def list_project_members(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all members of a project."""
    ProjectMember = _get_member_model()
    company_id = get_effective_company_id(current_user, db)
    members = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.company_id == company_id,
            ProjectMember.is_active == True,
        )
        .all()
    )
    return [
        {
            "id": m.id,
            "project_id": m.project_id,
            "user_id": m.user_id,
            "role": m.role,
            "is_active": m.is_active,
            "assigned_at": m.assigned_at.isoformat() if m.assigned_at else None,
            "assigned_by": m.assigned_by,
        }
        for m in members
    ]


@router.post("/projects/{project_id}/members", status_code=201)
async def add_project_member(
    project_id: int,
    data: AddMemberRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add a member to a project with a role."""
    ProjectMember = _get_member_model()
    company_id = get_effective_company_id(current_user, db)

    valid_roles = ["owner", "manager", "member", "viewer"]
    if data.role not in valid_roles:
        raise HTTPException(status_code=422, detail=f"Role must be one of: {valid_roles}")

    # Check if already a member
    existing = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == data.user_id,
        )
        .first()
    )
    if existing:
        existing.role = data.role
        existing.is_active = True
        existing.assigned_by = current_user.id
        db.commit()
        db.refresh(existing)
        return {"id": existing.id, "project_id": project_id, "user_id": data.user_id, "role": data.role}

    member = ProjectMember(
        project_id=project_id,
        user_id=data.user_id,
        company_id=company_id,
        role=data.role,
        assigned_by=current_user.id,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return {"id": member.id, "project_id": project_id, "user_id": data.user_id, "role": data.role}


@router.put("/project-members/{member_id}/role")
async def update_member_role(
    member_id: int,
    data: UpdateMemberRoleRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a project member's role."""
    ProjectMember = _get_member_model()
    company_id = get_effective_company_id(current_user, db)

    valid_roles = ["owner", "manager", "member", "viewer"]
    if data.role not in valid_roles:
        raise HTTPException(status_code=422, detail=f"Role must be one of: {valid_roles}")

    member = (
        db.query(ProjectMember)
        .filter(ProjectMember.id == member_id, ProjectMember.company_id == company_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.role = data.role
    db.commit()
    return {"id": member.id, "project_id": member.project_id, "user_id": member.user_id, "role": data.role}


@router.delete("/project-members/{member_id}", status_code=204)
async def remove_project_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Remove a member from a project (soft deactivate)."""
    ProjectMember = _get_member_model()
    company_id = get_effective_company_id(current_user, db)

    member = (
        db.query(ProjectMember)
        .filter(ProjectMember.id == member_id, ProjectMember.company_id == company_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.is_active = False
    db.commit()
