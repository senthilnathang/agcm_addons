"""Document service - business logic for folders and documents"""

import logging
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from addons.agcm_document.models.folder import ProjectFolder
from addons.agcm_document.models.document import ProjectDocument
from addons.agcm_document.schemas.document import (
    FolderCreate,
    FolderUpdate,
    DocumentCreate,
    DocumentUpdate,
)

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

# Sequence config for documents
SEQUENCE_PREFIX = "DOC"
SEQUENCE_PADDING = 5


def _next_doc_sequence(db: Session, company_id: int) -> str:
    """Generate next document sequence: DOC00001, DOC00002, etc."""
    import re

    last = (
        db.query(ProjectDocument.sequence_name)
        .filter(ProjectDocument.company_id == company_id)
        .filter(ProjectDocument.sequence_name.isnot(None))
        .order_by(ProjectDocument.id.desc())
        .first()
    )
    num = 1
    if last and last[0]:
        match = re.search(r"(\d+)$", last[0])
        if match:
            num = int(match.group(1)) + 1
    return f"{SEQUENCE_PREFIX}{num:0{SEQUENCE_PADDING}d}"


class DocumentService:
    """Handles folder and document CRUD with hierarchy support."""

    def __init__(self, db: Session, company_id: int, user_id: int):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id

    def _invalidate_document_cache(self, project_id: int = None):
        """Invalidate document-related cache."""
        if not CACHE_AVAILABLE:
            return

        if project_id:
            cache.invalidate_pattern_distributed(
                f"agcm_document:tree:{self.company_id}:{project_id}"
            )
            cache.invalidate_pattern_distributed(
                f"agcm_document:project:{self.company_id}:{project_id}:*"
            )
        cache.invalidate_pattern_distributed(f"agcm_document:*")

    # --- Folders ---

    def list_folders(self, project_id: int) -> List[ProjectFolder]:
        """List all folders for a project (flat list)."""
        return (
            self.db.query(ProjectFolder)
            .filter(
                ProjectFolder.project_id == project_id,
                ProjectFolder.company_id == self.company_id,
            )
            .order_by(ProjectFolder.name)
            .all()
        )

    def get_folder_tree(self, project_id: int) -> List[dict]:
        """Build hierarchical folder tree for a project."""
        folders = self.list_folders(project_id)

        # Count documents per folder
        doc_counts = dict(
            self.db.query(ProjectDocument.folder_id, func.count(ProjectDocument.id))
            .filter(
                ProjectDocument.project_id == project_id,
                ProjectDocument.company_id == self.company_id,
            )
            .group_by(ProjectDocument.folder_id)
            .all()
        )

        folder_map = {}
        for f in folders:
            folder_map[f.id] = {
                "id": f.id,
                "name": f.name,
                "parent_id": f.parent_id,
                "project_id": f.project_id,
                "created_at": f.created_at,
                "children": [],
                "document_count": doc_counts.get(f.id, 0),
            }

        roots = []
        for fid, fdata in folder_map.items():
            pid = fdata["parent_id"]
            if pid and pid in folder_map:
                folder_map[pid]["children"].append(fdata)
            else:
                roots.append(fdata)

        return roots

    def create_folder(self, data: FolderCreate) -> ProjectFolder:
        """Create a new folder."""
        folder = ProjectFolder(
            name=data.name,
            parent_id=data.parent_id,
            project_id=data.project_id,
            company_id=self.company_id,
            created_by=self.user_id,
        )
        self.db.add(folder)
        self.db.commit()
        self.db.refresh(folder)
        self._invalidate_document_cache(data.project_id)
        return folder

    def update_folder(
        self, folder_id: int, data: FolderUpdate
    ) -> Optional[ProjectFolder]:
        """Update a folder (rename or move)."""
        folder = (
            self.db.query(ProjectFolder)
            .filter(
                ProjectFolder.id == folder_id,
                ProjectFolder.company_id == self.company_id,
            )
            .first()
        )
        if not folder:
            return None

        project_id = folder.project_id
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(folder, key, value)
        folder.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(folder)
        self._invalidate_document_cache(project_id)
        return folder

    def delete_folder(self, folder_id: int) -> bool:
        """Delete a folder and cascade to child folders/documents."""
        folder = (
            self.db.query(ProjectFolder)
            .filter(
                ProjectFolder.id == folder_id,
                ProjectFolder.company_id == self.company_id,
            )
            .first()
        )
        if not folder:
            return False
        project_id = folder.project_id
        self.db.delete(folder)
        self.db.commit()
        self._invalidate_document_cache(project_id)
        return True

    # --- Documents ---

    def list_documents(
        self,
        project_id: int,
        folder_id: Optional[int] = None,
        document_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """List documents with filtering and pagination."""
        page_size = min(page_size, 200)
        query = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.company_id == self.company_id,
        )

        if folder_id is not None:
            query = query.filter(ProjectDocument.folder_id == folder_id)
        if document_type:
            query = query.filter(ProjectDocument.document_type == document_type)
        if status:
            query = query.filter(ProjectDocument.status == status)
        if search:
            term = f"%{search}%"
            query = query.filter(
                (ProjectDocument.name.ilike(term))
                | (ProjectDocument.description.ilike(term))
                | (ProjectDocument.sequence_name.ilike(term))
            )

        total = query.count()
        skip = (page - 1) * page_size
        items = (
            query.order_by(ProjectDocument.id.desc())
            .offset(skip)
            .limit(page_size)
            .all()
        )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_document(self, doc_id: int) -> Optional[ProjectDocument]:
        """Get a single document by ID."""
        return (
            self.db.query(ProjectDocument)
            .filter(
                ProjectDocument.id == doc_id,
                ProjectDocument.company_id == self.company_id,
            )
            .first()
        )

    def create_document(
        self,
        data: DocumentCreate,
        file_name: str = None,
        file_url: str = None,
        document_id: int = None,
    ) -> ProjectDocument:
        """Create a new document record."""
        doc = ProjectDocument(
            company_id=self.company_id,
            sequence_name=_next_doc_sequence(self.db, self.company_id),
            name=data.name,
            description=data.description,
            document_type=data.document_type or "other",
            status="draft",
            folder_id=data.folder_id,
            project_id=data.project_id,
            uploaded_by=self.user_id,
            file_name=file_name,
            file_url=file_url,
            document_id=document_id,
            created_by=self.user_id,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        self._invalidate_document_cache(data.project_id)
        return doc

    def update_document(
        self, doc_id: int, data: DocumentUpdate
    ) -> Optional[ProjectDocument]:
        """Update document metadata or status."""
        doc = self.get_document(doc_id)
        if not doc:
            return None

        project_id = doc.project_id
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(doc, key, value)
        doc.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(doc)
        self._invalidate_document_cache(project_id)
        return doc

    def delete_document(self, doc_id: int) -> bool:
        """Delete a document."""
        doc = self.get_document(doc_id)
        if not doc:
            return False
        project_id = doc.project_id
        self.db.delete(doc)
        self.db.commit()
        self._invalidate_document_cache(project_id)
        return True
