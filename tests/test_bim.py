"""Tests for agcm_bim module."""
import json

import pytest


@pytest.fixture
def M(load_model):
    return {
        "BIMModel": load_model("agcm_bim", "bim_model", "BIMModel"),
        "BIMViewpoint": load_model("agcm_bim", "bim_viewpoint", "BIMViewpoint"),
        "BIMElement": load_model("agcm_bim", "bim_element", "BIMElement"),
        "BIMAnnotation3D": load_model("agcm_bim", "annotation", "BIMAnnotation3D"),
        "ClashTest": load_model("agcm_bim", "clash_detection", "ClashTest"),
        "ClashResult": load_model("agcm_bim", "clash_detection", "ClashResult"),
    }


class TestBIMModel:
    def test_create_model(self, db, M, company_id, project_ids, user_id):
        m = M["BIMModel"](
            company_id=company_id, project_id=project_ids[0],
            name="Foundation Plan", file_format="ifc",
            file_name="foundation.ifc", file_size=15_000_000,
            discipline="structural", status="uploading",
            version=1, is_current=True, uploaded_by=user_id,
        )
        db.add(m); db.flush()
        assert m.id and m.status == "uploading"

    def test_model_formats(self, db, M, company_id, project_ids, user_id):
        formats = ["ifc", "rvt", "nwd", "fbx", "glb", "obj"]
        for fmt in formats:
            m = M["BIMModel"](
                company_id=company_id, project_id=project_ids[0],
                name=f"Test {fmt.upper()}", file_format=fmt,
                file_name=f"test.{fmt}", status="ready",
                version=1, is_current=True, uploaded_by=user_id,
            )
            db.add(m)
        db.flush()
        count = db.query(M["BIMModel"]).filter(
            M["BIMModel"].company_id == company_id
        ).count()
        assert count == 6

    def test_model_versioning(self, db, M, company_id, project_ids, user_id):
        v1 = M["BIMModel"](
            company_id=company_id, project_id=project_ids[0],
            name="HVAC Layout", file_format="ifc",
            version=1, is_current=False, status="ready",
            uploaded_by=user_id,
        )
        db.add(v1); db.flush()
        v2 = M["BIMModel"](
            company_id=company_id, project_id=project_ids[0],
            name="HVAC Layout", file_format="ifc",
            version=2, is_current=True, status="ready",
            parent_model_id=v1.id, uploaded_by=user_id,
        )
        db.add(v2); db.flush()
        assert v2.parent_model_id == v1.id
        assert v2.version == 2

    def test_model_xkt_fields(self, db, M, company_id, project_ids, user_id):
        m = M["BIMModel"](
            company_id=company_id, project_id=project_ids[0],
            name="MEP Model", file_format="ifc",
            xkt_file_url="/uploads/models/mep.xkt",
            file_size_xkt=5_000_000, status="ready",
            version=1, is_current=True, uploaded_by=user_id,
        )
        db.add(m); db.flush()
        assert m.xkt_file_url == "/uploads/models/mep.xkt"
        assert m.file_size_xkt == 5_000_000

    def test_model_federation_transforms(self, db, M, company_id, project_ids, user_id):
        m = M["BIMModel"](
            company_id=company_id, project_id=project_ids[0],
            name="Structural Model", file_format="ifc",
            position_x=10.5, position_y=20.0, position_z=0.0,
            rotation_x=0, rotation_y=0, rotation_z=45.0,
            scale_factor=1.0, status="ready",
            version=1, is_current=True, uploaded_by=user_id,
        )
        db.add(m); db.flush()
        assert m.position_x == 10.5
        assert m.rotation_z == 45.0

    def test_model_status_transitions(self, db, M, company_id, project_ids, user_id):
        for status in ["uploading", "processing", "ready", "failed", "archived"]:
            m = M["BIMModel"](
                company_id=company_id, project_id=project_ids[0],
                name=f"Status {status}", file_format="ifc",
                status=status, version=1, is_current=True,
                uploaded_by=user_id,
            )
            db.add(m)
        db.flush()
        count = db.query(M["BIMModel"]).filter(
            M["BIMModel"].company_id == company_id
        ).count()
        assert count == 5


class TestBIMViewpoint:
    def test_create_viewpoint(self, db, M, company_id, project_ids, user_id):
        model = M["BIMModel"](
            company_id=company_id, project_id=project_ids[0],
            name="Test Model", file_format="ifc",
            status="ready", version=1, is_current=True,
            uploaded_by=user_id,
        )
        db.add(model); db.flush()

        vp = M["BIMViewpoint"](
            company_id=company_id, model_id=model.id,
            name="Front Elevation",
            camera_position=json.dumps({"x": 0, "y": 0, "z": 50, "rx": 0, "ry": 0, "rz": 0}),
            camera_target=json.dumps({"x": 0, "y": 0, "z": 0}),
            created_by=user_id,
        )
        db.add(vp); db.flush()
        assert vp.id and vp.name == "Front Elevation"

    def test_viewpoint_with_bcf_data(self, db, M, company_id, project_ids, user_id):
        model = M["BIMModel"](
            company_id=company_id, project_id=project_ids[0],
            name="BCF Model", file_format="ifc",
            status="ready", version=1, is_current=True,
            uploaded_by=user_id,
        )
        db.add(model); db.flush()

        bcf = json.dumps({
            "perspective_camera": {"eye": [10, 10, 10], "look": [0, 0, 0], "up": [0, 1, 0]},
            "clipping_planes": [{"location": [0, 5, 0], "direction": [0, -1, 0]}],
            "components": {"selection": ["2O2Fr$t4X7Zf8NOew3FLOH"]},
        })
        vp = M["BIMViewpoint"](
            company_id=company_id, model_id=model.id,
            name="BCF Viewpoint", bcf_data=bcf,
            created_by=user_id,
        )
        db.add(vp); db.flush()
        assert json.loads(vp.bcf_data)["perspective_camera"]["eye"] == [10, 10, 10]

    def test_viewpoint_entity_link(self, db, M, company_id, project_ids, user_id):
        model = M["BIMModel"](
            company_id=company_id, project_id=project_ids[0],
            name="Linked Model", file_format="ifc",
            status="ready", version=1, is_current=True,
            uploaded_by=user_id,
        )
        db.add(model); db.flush()

        vp = M["BIMViewpoint"](
            company_id=company_id, model_id=model.id,
            name="RFI Viewpoint", entity_type="rfi", entity_id=42,
            linked_rfi_id=42, created_by=user_id,
        )
        db.add(vp); db.flush()
        assert vp.entity_type == "rfi"
        assert vp.linked_rfi_id == 42


class TestBIMElement:
    def test_create_element(self, db, M, company_id, project_ids, user_id):
        model = M["BIMModel"](
            company_id=company_id, project_id=project_ids[0],
            name="IFC Model", file_format="ifc",
            status="ready", version=1, is_current=True,
            uploaded_by=user_id,
        )
        db.add(model); db.flush()

        elem = M["BIMElement"](
            company_id=company_id, model_id=model.id,
            global_id="2O2Fr$t4X7Zf8NOew3FL",
            ifc_type="IfcWall", name="Exterior Wall A",
            material="Concrete", level="Level 1",
            discipline="architectural",
            bounding_box=json.dumps({"min": {"x": 0, "y": 0, "z": 0}, "max": {"x": 10, "y": 3, "z": 0.3}}),
        )
        db.add(elem); db.flush()
        assert elem.ifc_type == "IfcWall"

    def test_bulk_elements(self, db, M, company_id, project_ids, user_id):
        model = M["BIMModel"](
            company_id=company_id, project_id=project_ids[0],
            name="Bulk Model", file_format="ifc",
            status="ready", version=1, is_current=True,
            uploaded_by=user_id,
        )
        db.add(model); db.flush()

        ifc_types = ["IfcWall", "IfcDoor", "IfcWindow", "IfcSlab", "IfcColumn",
                      "IfcBeam", "IfcPipeSegment", "IfcDuctSegment"]
        for i, ifc_type in enumerate(ifc_types):
            elem = M["BIMElement"](
                company_id=company_id, model_id=model.id,
                global_id=f"ELEM{i:020d}",
                ifc_type=ifc_type, name=f"Element {i}",
            )
            db.add(elem)
        db.flush()
        count = db.query(M["BIMElement"]).filter(
            M["BIMElement"].model_id == model.id
        ).count()
        assert count == 8


class TestClashDetection:
    def test_create_clash_test(self, db, M, company_id, project_ids, user_id):
        m1 = M["BIMModel"](company_id=company_id, project_id=project_ids[0],
                           name="Structural", file_format="ifc", status="ready",
                           version=1, is_current=True, uploaded_by=user_id)
        m2 = M["BIMModel"](company_id=company_id, project_id=project_ids[0],
                           name="MEP", file_format="ifc", status="ready",
                           version=1, is_current=True, uploaded_by=user_id)
        db.add_all([m1, m2]); db.flush()

        ct = M["ClashTest"](
            company_id=company_id, project_id=project_ids[0],
            name="Structural vs MEP",
            model_a_id=m1.id, model_b_id=m2.id,
            test_type="hard", tolerance=0.01,
            status="pending",
        )
        db.add(ct); db.flush()
        assert ct.test_type == "hard"
        assert ct.status == "pending"

    def test_clash_results(self, db, M, company_id, project_ids, user_id):
        m1 = M["BIMModel"](company_id=company_id, project_id=project_ids[0],
                           name="Model A", file_format="ifc", status="ready",
                           version=1, is_current=True, uploaded_by=user_id)
        db.add(m1); db.flush()

        ct = M["ClashTest"](
            company_id=company_id, project_id=project_ids[0],
            name="Self Clash Test", model_a_id=m1.id,
            test_type="hard", status="completed",
            total_clashes=3, critical_count=1, major_count=1, minor_count=1,
        )
        db.add(ct); db.flush()

        severities = ["critical", "major", "minor"]
        for i, sev in enumerate(severities):
            cr = M["ClashResult"](
                clash_test_id=ct.id, company_id=company_id,
                element_a_id=f"ELEM_A_{i}", element_a_type="IfcPipeSegment",
                element_b_id=f"ELEM_B_{i}", element_b_type="IfcBeam",
                severity=sev, status="new",
                clash_point=json.dumps({"x": i * 5, "y": 2, "z": 3}),
                distance=0.05 * (i + 1),
            )
            db.add(cr)
        db.flush()
        count = db.query(M["ClashResult"]).filter(
            M["ClashResult"].clash_test_id == ct.id
        ).count()
        assert count == 3

    def test_clash_resolution_workflow(self, db, M, company_id, project_ids, user_id):
        m1 = M["BIMModel"](company_id=company_id, project_id=project_ids[0],
                           name="Workflow Model", file_format="ifc", status="ready",
                           version=1, is_current=True, uploaded_by=user_id)
        db.add(m1); db.flush()

        ct = M["ClashTest"](
            company_id=company_id, project_id=project_ids[0],
            name="Resolution Test", model_a_id=m1.id,
            test_type="hard", status="completed",
        )
        db.add(ct); db.flush()

        cr = M["ClashResult"](
            clash_test_id=ct.id, company_id=company_id,
            element_a_id="A1", element_a_type="IfcDuctSegment",
            element_b_id="B1", element_b_type="IfcColumn",
            severity="critical", status="new",
            assigned_to=user_id,
        )
        db.add(cr); db.flush()
        assert cr.status == "new"

        # Simulate resolution workflow
        for status in ["active", "reviewed", "resolved"]:
            cr.status = status
            db.flush()
        assert cr.status == "resolved"

    def test_clash_test_types(self, db, M, company_id, project_ids, user_id):
        m1 = M["BIMModel"](company_id=company_id, project_id=project_ids[0],
                           name="Type Test Model", file_format="ifc", status="ready",
                           version=1, is_current=True, uploaded_by=user_id)
        db.add(m1); db.flush()

        for test_type in ["hard", "soft", "clearance", "duplicate"]:
            ct = M["ClashTest"](
                company_id=company_id, project_id=project_ids[0],
                name=f"{test_type.title()} Test",
                model_a_id=m1.id, test_type=test_type,
                tolerance=0.05, status="pending",
            )
            db.add(ct)
        db.flush()
        count = db.query(M["ClashTest"]).filter(
            M["ClashTest"].project_id == project_ids[0]
        ).count()
        assert count == 4


class TestBIMAnnotation:
    def test_create_annotation(self, db, M, company_id, project_ids, user_id):
        model = M["BIMModel"](
            company_id=company_id, project_id=project_ids[0],
            name="Annotated Model", file_format="ifc",
            status="ready", version=1, is_current=True,
            uploaded_by=user_id,
        )
        db.add(model); db.flush()

        ann = M["BIMAnnotation3D"](
            company_id=company_id, project_id=project_ids[0],
            model_id=model.id,
            world_pos_x=5.0, world_pos_y=2.5, world_pos_z=3.0,
            eye_x=10, eye_y=10, eye_z=10,
            look_x=5, look_y=2.5, look_z=3,
            title="Check rebar spacing",
            description="Rebar spacing appears inconsistent at this column joint",
            priority="high", status="open",
            assigned_to=user_id,
        )
        db.add(ann); db.flush()
        assert ann.title == "Check rebar spacing"
        assert ann.priority == "high"

    def test_annotation_entity_link(self, db, M, company_id, project_ids, user_id):
        model = M["BIMModel"](
            company_id=company_id, project_id=project_ids[0],
            name="Link Model", file_format="ifc",
            status="ready", version=1, is_current=True,
            uploaded_by=user_id,
        )
        db.add(model); db.flush()

        ann = M["BIMAnnotation3D"](
            company_id=company_id, project_id=project_ids[0],
            model_id=model.id,
            world_pos_x=1.0, world_pos_y=1.0, world_pos_z=1.0,
            title="Linked to Issue #5",
            linked_entity_type="issue", linked_entity_id=5,
            status="open",
        )
        db.add(ann); db.flush()
        assert ann.linked_entity_type == "issue"
        assert ann.linked_entity_id == 5

    def test_annotation_statuses(self, db, M, company_id, project_ids, user_id):
        model = M["BIMModel"](
            company_id=company_id, project_id=project_ids[0],
            name="Status Model", file_format="ifc",
            status="ready", version=1, is_current=True,
            uploaded_by=user_id,
        )
        db.add(model); db.flush()

        for status in ["open", "in_progress", "resolved"]:
            ann = M["BIMAnnotation3D"](
                company_id=company_id, project_id=project_ids[0],
                model_id=model.id,
                world_pos_x=0, world_pos_y=0, world_pos_z=0,
                title=f"Annotation {status}", status=status,
            )
            db.add(ann)
        db.flush()
        count = db.query(M["BIMAnnotation3D"]).filter(
            M["BIMAnnotation3D"].project_id == project_ids[0]
        ).count()
        assert count == 3
