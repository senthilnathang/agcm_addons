"""Lookup/configuration tables for AG CM module"""

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class Trade(Base, TimestampMixin):
    """Trade list (e.g. Electrical, Plumbing, HVAC)"""
    __tablename__ = "agcm_trades"
    _description = "Construction trade classifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company = relationship("Company", foreign_keys=[company_id], lazy="select")


class InspectionType(Base, TimestampMixin):
    """Inspection type classification"""
    __tablename__ = "agcm_inspection_types"
    _description = "Third-party inspection type classifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company = relationship("Company", foreign_keys=[company_id], lazy="select")


class AccidentType(Base, TimestampMixin):
    """Accident type classification"""
    __tablename__ = "agcm_accident_types"
    _description = "Accident type classifications for incident reporting"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company = relationship("Company", foreign_keys=[company_id], lazy="select")


class ViolationType(Base, TimestampMixin):
    """Safety violation/observation type"""
    __tablename__ = "agcm_violation_types"
    _description = "Safety observation type classifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company = relationship("Company", foreign_keys=[company_id], lazy="select")
