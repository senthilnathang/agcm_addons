"""Generic commenting system for any AGCM entity."""

from sqlalchemy import Column, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.base import TimestampMixin


class EntityComment(Base, TimestampMixin):
    """Generic comment attached to any entity across all AGCM modules."""
    __tablename__ = "agcm_entity_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)  # "rfi", "submittal", "change_order", etc.
    entity_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_name = Column(String(255), nullable=True)  # denormalized for display
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)  # internal note vs public comment
    parent_id = Column(Integer, ForeignKey("agcm_entity_comments.id", ondelete="CASCADE"), nullable=True)  # threading
    mentioned_user_ids = Column(Text, nullable=True)  # JSON array of user IDs mentioned with @
