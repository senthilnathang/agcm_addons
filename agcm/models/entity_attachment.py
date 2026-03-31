"""Generic entity-attachment linking table for cross-module document references."""

from sqlalchemy import Column, ForeignKey, Integer, String, Table

from app.db.base import Base

# Generic M2M linking any entity to documents
agcm_entity_attachments = Table(
    "agcm_entity_attachments",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("entity_type", String(100), nullable=False),  # "rfi", "submittal", "change_order", etc.
    Column("entity_id", Integer, nullable=False),
    Column("document_id", Integer, ForeignKey("agcm_project_documents.id", ondelete="CASCADE"), nullable=False),
    Column("company_id", Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
)
