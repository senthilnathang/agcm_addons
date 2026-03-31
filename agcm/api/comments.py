"""Generic commenting API for any AGCM entity."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_effective_company_id
from addons.agcm.models.comment import EntityComment

router = APIRouter()


class CommentCreate(BaseModel):
    entity_type: str = Field(..., max_length=100)
    entity_id: int
    content: str = Field(..., min_length=1)
    is_internal: bool = False
    parent_id: Optional[int] = None
    mentioned_user_ids: Optional[str] = None  # JSON array string


class CommentUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)
    is_internal: Optional[bool] = None
    mentioned_user_ids: Optional[str] = None


class CommentResponse(BaseModel):
    id: int
    company_id: int
    entity_type: str
    entity_id: int
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    content: str
    is_internal: bool = False
    parent_id: Optional[int] = None
    mentioned_user_ids: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/comments")
async def list_comments(
    entity_type: str = Query(...),
    entity_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List comments for a given entity."""
    company_id = get_effective_company_id(current_user, db)
    comments = (
        db.query(EntityComment)
        .filter(
            EntityComment.company_id == company_id,
            EntityComment.entity_type == entity_type,
            EntityComment.entity_id == entity_id,
        )
        .order_by(EntityComment.id.asc())
        .all()
    )
    return [
        {c.key: getattr(comment, c.key) for c in comment.__table__.columns}
        for comment in comments
    ]


@router.post("/comments", status_code=201)
async def create_comment(
    data: CommentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a comment on any entity."""
    company_id = get_effective_company_id(current_user, db)
    user_name = getattr(current_user, "full_name", None) or getattr(current_user, "email", None)
    comment = EntityComment(
        company_id=company_id,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        user_id=current_user.id,
        user_name=user_name,
        content=data.content,
        is_internal=data.is_internal,
        parent_id=data.parent_id,
        mentioned_user_ids=data.mentioned_user_ids,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return {c.key: getattr(comment, c.key) for c in comment.__table__.columns}


@router.put("/comments/{comment_id}")
async def update_comment(
    comment_id: int,
    data: CommentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Edit a comment."""
    company_id = get_effective_company_id(current_user, db)
    comment = (
        db.query(EntityComment)
        .filter(
            EntityComment.id == comment_id,
            EntityComment.company_id == company_id,
        )
        .first()
    )
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(comment, key, value)

    db.commit()
    db.refresh(comment)
    return {c.key: getattr(comment, c.key) for c in comment.__table__.columns}


@router.delete("/comments/{comment_id}", status_code=204)
async def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a comment."""
    company_id = get_effective_company_id(current_user, db)
    comment = (
        db.query(EntityComment)
        .filter(
            EntityComment.id == comment_id,
            EntityComment.company_id == company_id,
        )
        .first()
    )
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    db.delete(comment)
    db.commit()
