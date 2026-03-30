"""RFI Response model - threaded responses to RFIs"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Text, Index
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class RFIResponse(Base, TimestampMixin):
    """Threaded response to an RFI."""
    __tablename__ = "agcm_rfi_responses"
    _description = "RFI threaded responses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    rfi_id = Column(
        Integer,
        ForeignKey("agcm_rfis.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    parent_id = Column(
        Integer,
        ForeignKey("agcm_rfi_responses.id", ondelete="CASCADE"),
        nullable=True,
    )

    content = Column(Text, nullable=False)
    is_official_response = Column(Boolean, default=False, nullable=False)

    responded_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    company = relationship("Company", foreign_keys=[company_id], lazy="select")
    rfi = relationship("RFI", back_populates="responses", lazy="select")
    replies = relationship(
        "RFIResponse",
        lazy="select",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_agcm_rfi_response_rfi", "rfi_id"),
    )
