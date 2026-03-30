"""Tests for the agcm_document module — ProjectFolder and ProjectDocument models."""

import pytest
from datetime import date


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _folder_cls(load_model):
    return load_model("agcm_document", "folder", "ProjectFolder")


def _doc_cls(load_model):
    return load_model("agcm_document", "document", "ProjectDocument")


def _doc_type_enum(load_model):
    return load_model("agcm_document", "document", "DocumentType")


def _doc_status_enum(load_model):
    return load_model("agcm_document", "document", "DocumentStatus")


# ---------------------------------------------------------------------------
# Folder tests
# ---------------------------------------------------------------------------

class TestProjectFolder:

    def test_create_folder(self, db, load_model, project_ids, company_id, user_id):
        ProjectFolder = _folder_cls(load_model)
        folder = ProjectFolder(
            name="Test Folder",
            project_id=project_ids[0],
            company_id=company_id,
            created_by=user_id,
        )
        db.add(folder)
        db.flush()

        assert folder.id is not None
        assert folder.name == "Test Folder"
        assert folder.project_id == project_ids[0]
        assert folder.parent_id is None

    def test_create_nested_folders(self, db, load_model, project_ids, company_id, user_id):
        ProjectFolder = _folder_cls(load_model)

        parent = ProjectFolder(
            name="Parent Folder",
            project_id=project_ids[0],
            company_id=company_id,
            created_by=user_id,
        )
        db.add(parent)
        db.flush()

        child = ProjectFolder(
            name="Child Folder",
            project_id=project_ids[0],
            company_id=company_id,
            parent_id=parent.id,
            created_by=user_id,
        )
        db.add(child)
        db.flush()

        assert child.parent_id == parent.id
        assert child.id != parent.id

    def test_folder_tree_structure(self, db, load_model, project_ids, company_id, user_id):
        """Create a 3-level hierarchy and verify relationships."""
        ProjectFolder = _folder_cls(load_model)

        root = ProjectFolder(name="Root", project_id=project_ids[0], company_id=company_id, created_by=user_id)
        db.add(root)
        db.flush()

        mid = ProjectFolder(name="Mid", project_id=project_ids[0], company_id=company_id, parent_id=root.id, created_by=user_id)
        db.add(mid)
        db.flush()

        leaf = ProjectFolder(name="Leaf", project_id=project_ids[0], company_id=company_id, parent_id=mid.id, created_by=user_id)
        db.add(leaf)
        db.flush()

        assert leaf.parent_id == mid.id
        assert mid.parent_id == root.id
        assert root.parent_id is None

    def test_delete_folder_cascades_docs(self, db, load_model, project_ids, company_id, user_id):
        """Deleting a folder cascade-deletes its documents via the
        'all, delete-orphan' relationship on ProjectFolder.documents."""
        ProjectFolder = _folder_cls(load_model)
        ProjectDocument = _doc_cls(load_model)

        folder = ProjectFolder(name="Doomed Folder", project_id=project_ids[0], company_id=company_id, created_by=user_id)
        db.add(folder)
        db.flush()

        doc = ProjectDocument(
            name="Doomed Doc",
            project_id=project_ids[0],
            company_id=company_id,
            folder_id=folder.id,
        )
        db.add(doc)
        db.flush()
        doc_id = doc.id

        db.delete(folder)
        db.flush()

        # The ORM cascade="all, delete-orphan" removes child documents
        found = db.get(ProjectDocument, doc_id)
        assert found is None


# ---------------------------------------------------------------------------
# Document tests
# ---------------------------------------------------------------------------

class TestProjectDocument:

    def test_create_document(self, db, load_model, project_ids, company_id):
        ProjectDocument = _doc_cls(load_model)
        DocumentType = _doc_type_enum(load_model)
        DocumentStatus = _doc_status_enum(load_model)

        doc = ProjectDocument(
            name="Foundation Plan Rev A",
            description="Structural foundation drawings",
            document_type=DocumentType.BLUEPRINT,
            status=DocumentStatus.DRAFT,
            revision=1,
            file_name="foundation_plan_a.pdf",
            file_url="/uploads/docs/foundation_plan_a.pdf",
            project_id=project_ids[0],
            company_id=company_id,
            sequence_name="DOC00001",
        )
        db.add(doc)
        db.flush()

        assert doc.id is not None
        assert doc.sequence_name == "DOC00001"
        assert doc.document_type == DocumentType.BLUEPRINT
        assert doc.status == DocumentStatus.DRAFT
        assert doc.revision == 1

    def test_document_types(self, db, load_model, project_ids, company_id):
        ProjectDocument = _doc_cls(load_model)
        DocumentType = _doc_type_enum(load_model)

        for dtype in DocumentType:
            doc = ProjectDocument(
                name=f"Doc {dtype.value}",
                document_type=dtype,
                project_id=project_ids[0],
                company_id=company_id,
            )
            db.add(doc)
            db.flush()
            assert doc.document_type == dtype

    def test_document_status_workflow(self, db, load_model, project_ids, company_id):
        ProjectDocument = _doc_cls(load_model)
        DocumentStatus = _doc_status_enum(load_model)

        doc = ProjectDocument(
            name="Workflow Doc",
            project_id=project_ids[0],
            company_id=company_id,
            status=DocumentStatus.DRAFT,
        )
        db.add(doc)
        db.flush()
        assert doc.status == DocumentStatus.DRAFT

        doc.status = DocumentStatus.UNDER_REVIEW
        db.flush()
        assert doc.status == DocumentStatus.UNDER_REVIEW

        doc.status = DocumentStatus.APPROVED
        db.flush()
        assert doc.status == DocumentStatus.APPROVED

    def test_list_documents_pagination(self, db, load_model, project_ids, company_id):
        ProjectDocument = _doc_cls(load_model)

        for i in range(5):
            db.add(ProjectDocument(
                name=f"Paginated Doc {i}",
                project_id=project_ids[0],
                company_id=company_id,
            ))
        db.flush()

        page1 = (
            db.query(ProjectDocument)
            .filter(ProjectDocument.project_id == project_ids[0])
            .limit(2)
            .all()
        )
        assert len(page1) == 2

        page2 = (
            db.query(ProjectDocument)
            .filter(ProjectDocument.project_id == project_ids[0])
            .offset(2)
            .limit(2)
            .all()
        )
        assert len(page2) == 2

        total = (
            db.query(ProjectDocument)
            .filter(ProjectDocument.project_id == project_ids[0])
            .count()
        )
        assert total == 5

    def test_list_documents_filter_by_type(self, db, load_model, project_ids, company_id):
        ProjectDocument = _doc_cls(load_model)
        DocumentType = _doc_type_enum(load_model)

        db.add(ProjectDocument(name="Blueprint", document_type=DocumentType.BLUEPRINT, project_id=project_ids[0], company_id=company_id))
        db.add(ProjectDocument(name="Contract", document_type=DocumentType.CONTRACT, project_id=project_ids[0], company_id=company_id))
        db.add(ProjectDocument(name="Blueprint 2", document_type=DocumentType.BLUEPRINT, project_id=project_ids[0], company_id=company_id))
        db.flush()

        blueprints = (
            db.query(ProjectDocument)
            .filter(ProjectDocument.document_type == DocumentType.BLUEPRINT)
            .filter(ProjectDocument.project_id == project_ids[0])
            .all()
        )
        assert len(blueprints) == 2

    def test_list_documents_filter_by_folder(self, db, load_model, project_ids, company_id, user_id):
        ProjectFolder = _folder_cls(load_model)
        ProjectDocument = _doc_cls(load_model)

        f1 = ProjectFolder(name="Folder A", project_id=project_ids[0], company_id=company_id, created_by=user_id)
        f2 = ProjectFolder(name="Folder B", project_id=project_ids[0], company_id=company_id, created_by=user_id)
        db.add_all([f1, f2])
        db.flush()

        db.add(ProjectDocument(name="Doc in A", folder_id=f1.id, project_id=project_ids[0], company_id=company_id))
        db.add(ProjectDocument(name="Doc in B", folder_id=f2.id, project_id=project_ids[0], company_id=company_id))
        db.add(ProjectDocument(name="Doc in A2", folder_id=f1.id, project_id=project_ids[0], company_id=company_id))
        db.flush()

        docs_in_a = (
            db.query(ProjectDocument)
            .filter(ProjectDocument.folder_id == f1.id)
            .all()
        )
        assert len(docs_in_a) == 2

    def test_update_document(self, db, load_model, project_ids, company_id):
        ProjectDocument = _doc_cls(load_model)
        DocumentStatus = _doc_status_enum(load_model)

        doc = ProjectDocument(
            name="Original Name",
            project_id=project_ids[0],
            company_id=company_id,
            status=DocumentStatus.DRAFT,
        )
        db.add(doc)
        db.flush()

        doc.name = "Updated Name"
        doc.status = DocumentStatus.APPROVED
        db.flush()

        refreshed = db.get(ProjectDocument, doc.id)
        assert refreshed.name == "Updated Name"
        assert refreshed.status == DocumentStatus.APPROVED

    def test_delete_document(self, db, load_model, project_ids, company_id):
        ProjectDocument = _doc_cls(load_model)

        doc = ProjectDocument(name="To Delete", project_id=project_ids[0], company_id=company_id)
        db.add(doc)
        db.flush()
        doc_id = doc.id

        db.delete(doc)
        db.flush()

        assert db.get(ProjectDocument, doc_id) is None

    def test_document_search(self, db, load_model, project_ids, company_id):
        ProjectDocument = _doc_cls(load_model)

        db.add(ProjectDocument(name="Foundation Plan", project_id=project_ids[0], company_id=company_id))
        db.add(ProjectDocument(name="Roof Plan", project_id=project_ids[0], company_id=company_id))
        db.add(ProjectDocument(name="Foundation Detail", project_id=project_ids[0], company_id=company_id))
        db.flush()

        results = (
            db.query(ProjectDocument)
            .filter(ProjectDocument.name.ilike("%foundation%"))
            .all()
        )
        assert len(results) == 2
