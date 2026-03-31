"""BIM service - business logic for models, viewpoints, clashes, and elements"""

import json
import logging
import re
import time
from datetime import date, datetime
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from addons.agcm_bim.models.bim_model import BIMModel, BIMModelStatus
from addons.agcm_bim.models.bim_viewpoint import BIMViewpoint
from addons.agcm_bim.models.clash_detection import (
    ClashTest, ClashTestStatus, ClashSeverity, ClashStatus, ClashResult,
)
from addons.agcm_bim.models.bim_element import BIMElement
from addons.agcm_bim.schemas.bim import (
    BIMModelCreate, BIMModelUpdate,
    BIMViewpointCreate, BIMViewpointUpdate,
    ClashTestCreate, ClashTestUpdate,
    ClashResultUpdate, ClashResultResolve, ClashResultAssign,
)

logger = logging.getLogger(__name__)

# Sequence configs: (prefix, padding)
SEQ_MODEL = ("BIM", 5)
SEQ_CLASH_TEST = ("CT", 5)
SEQ_CLASH_RESULT = ("CL", 5)


def _next_seq(db: Session, model_class, company_id: int, prefix: str, padding: int) -> str:
    """Generate next sequence name for a model."""
    last = (
        db.query(model_class.sequence_name)
        .filter(model_class.company_id == company_id, model_class.sequence_name.isnot(None))
        .order_by(model_class.id.desc())
        .first()
    )
    num = 1
    if last and last[0]:
        match = re.search(r'(\d+)$', last[0])
        if match:
            num = int(match.group(1)) + 1
    return f"{prefix}{num:0{padding}d}"


class BIMService:
    """Handles BIM model CRUD, viewpoints, clash detection, and element search."""

    def __init__(self, db: Session, company_id: int, user_id: int):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id

    # ─── BIM Model CRUD ──────────────────────────────────────────────────

    def list_models(
        self,
        project_id: Optional[int] = None,
        discipline: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        current_only: bool = True,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        page_size = min(page_size, 200)
        query = self.db.query(BIMModel).filter(BIMModel.company_id == self.company_id)

        if project_id:
            query = query.filter(BIMModel.project_id == project_id)
        if discipline:
            query = query.filter(BIMModel.discipline == discipline)
        if status:
            query = query.filter(BIMModel.status == status)
        if current_only:
            query = query.filter(BIMModel.is_current == True)
        if search:
            term = f"%{search}%"
            query = query.filter(
                (BIMModel.name.ilike(term)) | (BIMModel.sequence_name.ilike(term))
            )

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(BIMModel.id.desc()).offset(skip).limit(page_size).all()

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_model(self, model_id: int) -> Optional[BIMModel]:
        return (
            self.db.query(BIMModel)
            .filter(BIMModel.id == model_id, BIMModel.company_id == self.company_id)
            .first()
        )

    def get_model_detail(self, model_id: int) -> Optional[dict]:
        model = self.get_model(model_id)
        if not model:
            return None

        viewpoint_count = (
            self.db.query(func.count(BIMViewpoint.id))
            .filter(BIMViewpoint.model_id == model_id)
            .scalar() or 0
        )

        # Version history
        version_history = []
        if model.parent_model_id:
            versions = (
                self.db.query(BIMModel)
                .filter(
                    BIMModel.company_id == self.company_id,
                    ((BIMModel.parent_model_id == model.parent_model_id) |
                     (BIMModel.id == model.parent_model_id))
                )
                .order_by(BIMModel.version.desc())
                .all()
            )
            version_history = [
                {"id": v.id, "version": v.version, "name": v.name,
                 "is_current": v.is_current, "created_at": str(v.created_at) if v.created_at else None}
                for v in versions
            ]

        # Element summary
        element_summary = self._get_model_summary_dict(model_id)

        return {
            **{c.key: getattr(model, c.key) for c in model.__table__.columns},
            "viewpoint_count": viewpoint_count,
            "version_history": version_history,
            "element_summary": element_summary,
        }

    def create_model(self, data: BIMModelCreate) -> BIMModel:
        model = BIMModel(
            company_id=self.company_id,
            sequence_name=_next_seq(self.db, BIMModel, self.company_id, *SEQ_MODEL),
            name=data.name,
            description=data.description,
            discipline=data.discipline,
            file_format=data.file_format,
            project_id=data.project_id,
            uploaded_by=self.user_id,
            created_by=self.user_id,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def update_model(self, model_id: int, data: BIMModelUpdate) -> Optional[BIMModel]:
        model = self.get_model(model_id)
        if not model:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(model, key, value)
        model.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(model)
        return model

    def delete_model(self, model_id: int) -> bool:
        model = self.get_model(model_id)
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True

    def update_model_file(
        self, model_id: int, file_url: str, file_name: str, file_size: int
    ) -> Optional[BIMModel]:
        """Update model with uploaded file info and set status to processing."""
        model = self.get_model(model_id)
        if not model:
            return None

        # Derive format from extension
        ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        format_map = {
            "ifc": "ifc", "rvt": "rvt", "nwd": "nwd", "nwc": "nwd",
            "fbx": "fbx", "glb": "glb", "gltf": "glb", "obj": "obj",
        }

        model.file_url = file_url
        model.file_name = file_name
        model.file_size = file_size
        model.file_format = format_map.get(ext, ext)
        model.status = BIMModelStatus.PROCESSING
        model.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(model)
        return model

    def process_model(self, model_id: int) -> Optional[BIMModel]:
        """
        Process uploaded model: extract metadata and count elements.
        In production this would parse IFC with ifcopenshell; here we set ready status.
        """
        model = self.get_model(model_id)
        if not model:
            return None

        try:
            # Count existing elements for this model
            element_count = (
                self.db.query(func.count(BIMElement.id))
                .filter(BIMElement.model_id == model_id)
                .scalar() or 0
            )
            model.element_count = element_count
            model.status = BIMModelStatus.READY
            model.processing_error = None
        except Exception as e:
            model.status = BIMModelStatus.FAILED
            model.processing_error = str(e)
            logger.error(f"Failed to process BIM model {model_id}: {e}")

        model.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(model)
        return model

    def create_model_version(self, model_id: int) -> Optional[BIMModel]:
        """Create a new version of an existing model (version chain via parent_model_id)."""
        original = self.get_model(model_id)
        if not original:
            return None

        # Determine root of version chain
        root_id = original.parent_model_id or original.id

        # Find highest version in chain
        max_version = (
            self.db.query(func.max(BIMModel.version))
            .filter(
                BIMModel.company_id == self.company_id,
                ((BIMModel.parent_model_id == root_id) | (BIMModel.id == root_id))
            )
            .scalar() or 1
        )

        # Mark all versions as non-current
        (
            self.db.query(BIMModel)
            .filter(
                BIMModel.company_id == self.company_id,
                ((BIMModel.parent_model_id == root_id) | (BIMModel.id == root_id))
            )
            .update({"is_current": False}, synchronize_session="fetch")
        )

        # Create new version
        new_model = BIMModel(
            company_id=self.company_id,
            sequence_name=_next_seq(self.db, BIMModel, self.company_id, *SEQ_MODEL),
            name=original.name,
            description=original.description,
            discipline=original.discipline,
            file_format=original.file_format,
            project_id=original.project_id,
            version=max_version + 1,
            is_current=True,
            parent_model_id=root_id,
            uploaded_by=self.user_id,
            created_by=self.user_id,
        )
        self.db.add(new_model)
        self.db.commit()
        self.db.refresh(new_model)
        return new_model

    def get_model_versions(self, model_id: int) -> List[BIMModel]:
        """Get all versions of a model."""
        model = self.get_model(model_id)
        if not model:
            return []
        root_id = model.parent_model_id or model.id
        return (
            self.db.query(BIMModel)
            .filter(
                BIMModel.company_id == self.company_id,
                ((BIMModel.parent_model_id == root_id) | (BIMModel.id == root_id))
            )
            .order_by(BIMModel.version.desc())
            .all()
        )

    # ─── Viewpoint CRUD ──────────────────────────────────────────────────

    def list_viewpoints(
        self,
        model_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        page_size = min(page_size, 200)
        query = self.db.query(BIMViewpoint).filter(BIMViewpoint.company_id == self.company_id)

        if model_id:
            query = query.filter(BIMViewpoint.model_id == model_id)
        if entity_type:
            query = query.filter(BIMViewpoint.entity_type == entity_type)
        if entity_id is not None:
            query = query.filter(BIMViewpoint.entity_id == entity_id)

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(BIMViewpoint.id.desc()).offset(skip).limit(page_size).all()

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_viewpoint(self, viewpoint_id: int) -> Optional[BIMViewpoint]:
        return (
            self.db.query(BIMViewpoint)
            .filter(BIMViewpoint.id == viewpoint_id, BIMViewpoint.company_id == self.company_id)
            .first()
        )

    def create_viewpoint(self, data: BIMViewpointCreate) -> BIMViewpoint:
        vp = BIMViewpoint(
            company_id=self.company_id,
            model_id=data.model_id,
            name=data.name,
            description=data.description,
            camera_position=data.camera_position,
            camera_target=data.camera_target,
            section_planes=data.section_planes,
            visible_elements=data.visible_elements,
            hidden_elements=data.hidden_elements,
            annotations=data.annotations,
            screenshot_url=data.screenshot_url,
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            created_by=self.user_id,
        )
        self.db.add(vp)
        self.db.commit()
        self.db.refresh(vp)
        return vp

    def update_viewpoint(self, viewpoint_id: int, data: BIMViewpointUpdate) -> Optional[BIMViewpoint]:
        vp = self.get_viewpoint(viewpoint_id)
        if not vp:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(vp, key, value)

        self.db.commit()
        self.db.refresh(vp)
        return vp

    def delete_viewpoint(self, viewpoint_id: int) -> bool:
        vp = self.get_viewpoint(viewpoint_id)
        if not vp:
            return False
        self.db.delete(vp)
        self.db.commit()
        return True

    # ─── Clash Test CRUD ─────────────────────────────────────────────────

    def list_clash_tests(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        page_size = min(page_size, 200)
        query = self.db.query(ClashTest).filter(ClashTest.company_id == self.company_id)

        if project_id:
            query = query.filter(ClashTest.project_id == project_id)
        if status:
            query = query.filter(ClashTest.status == status)

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(ClashTest.id.desc()).offset(skip).limit(page_size).all()

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_clash_test(self, test_id: int) -> Optional[ClashTest]:
        return (
            self.db.query(ClashTest)
            .filter(ClashTest.id == test_id, ClashTest.company_id == self.company_id)
            .first()
        )

    def get_clash_test_detail(self, test_id: int) -> Optional[dict]:
        test = self.get_clash_test(test_id)
        if not test:
            return None

        results = (
            self.db.query(ClashResult)
            .filter(ClashResult.clash_test_id == test_id)
            .order_by(ClashResult.severity, ClashResult.id)
            .limit(500)
            .all()
        )

        result_dicts = [
            {c.key: getattr(r, c.key) for c in r.__table__.columns}
            for r in results
        ]

        model_a_name = None
        model_b_name = None
        if test.model_a_id:
            ma = self.db.query(BIMModel.name).filter(BIMModel.id == test.model_a_id).first()
            model_a_name = ma[0] if ma else None
        if test.model_b_id:
            mb = self.db.query(BIMModel.name).filter(BIMModel.id == test.model_b_id).first()
            model_b_name = mb[0] if mb else None

        return {
            **{c.key: getattr(test, c.key) for c in test.__table__.columns},
            "model_a_name": model_a_name,
            "model_b_name": model_b_name,
            "results": result_dicts,
        }

    def create_clash_test(self, data: ClashTestCreate) -> ClashTest:
        test = ClashTest(
            company_id=self.company_id,
            sequence_name=_next_seq(self.db, ClashTest, self.company_id, *SEQ_CLASH_TEST),
            name=data.name,
            description=data.description,
            project_id=data.project_id,
            model_a_id=data.model_a_id,
            model_b_id=data.model_b_id,
            test_type=data.test_type or "hard",
            tolerance=data.tolerance if data.tolerance is not None else 0.01,
            created_by=self.user_id,
        )
        self.db.add(test)
        self.db.commit()
        self.db.refresh(test)
        return test

    def update_clash_test(self, test_id: int, data: ClashTestUpdate) -> Optional[ClashTest]:
        test = self.get_clash_test(test_id)
        if not test:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(test, key, value)
        test.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(test)
        return test

    def delete_clash_test(self, test_id: int) -> bool:
        test = self.get_clash_test(test_id)
        if not test:
            return False
        self.db.delete(test)
        self.db.commit()
        return True

    def run_clash_test(self, test_id: int) -> Optional[ClashTest]:
        """
        Run clash detection between two models using AABB overlap.

        Algorithm:
        1. Load bounding boxes of all elements from both models.
        2. Check for axis-aligned bounding box (AABB) overlaps.
        3. Filter by tolerance.
        4. Classify severity based on overlap distance.
        5. Create ClashResult records.
        """
        test = self.get_clash_test(test_id)
        if not test:
            return None
        if not test.model_a_id:
            test.status = ClashTestStatus.FAILED
            self.db.commit()
            return test

        test.status = ClashTestStatus.RUNNING
        test.run_date = datetime.utcnow()
        self.db.flush()

        start_time = time.time()

        try:
            # Load elements with bounding boxes from model A
            elements_a = (
                self.db.query(BIMElement)
                .filter(
                    BIMElement.model_id == test.model_a_id,
                    BIMElement.bounding_box.isnot(None),
                )
                .all()
            )

            # Load elements from model B (or same model for self-clash)
            model_b_id = test.model_b_id or test.model_a_id
            is_self_clash = (model_b_id == test.model_a_id)

            elements_b = (
                self.db.query(BIMElement)
                .filter(
                    BIMElement.model_id == model_b_id,
                    BIMElement.bounding_box.isnot(None),
                )
                .all()
            )

            # Parse bounding boxes
            def parse_bbox(el):
                try:
                    bb = json.loads(el.bounding_box)
                    return {
                        "min_x": bb["min"]["x"], "min_y": bb["min"]["y"], "min_z": bb["min"]["z"],
                        "max_x": bb["max"]["x"], "max_y": bb["max"]["y"], "max_z": bb["max"]["z"],
                    }
                except (json.JSONDecodeError, KeyError, TypeError):
                    return None

            bboxes_a = [(el, parse_bbox(el)) for el in elements_a]
            bboxes_a = [(el, bb) for el, bb in bboxes_a if bb]

            bboxes_b = [(el, parse_bbox(el)) for el in elements_b]
            bboxes_b = [(el, bb) for el, bb in bboxes_b if bb]

            tolerance = test.tolerance or 0.01
            clash_count = 0
            critical = 0
            major = 0
            minor = 0

            # Delete previous results
            self.db.query(ClashResult).filter(ClashResult.clash_test_id == test_id).delete()

            # AABB overlap check
            for el_a, bb_a in bboxes_a:
                for el_b, bb_b in bboxes_b:
                    # Skip self-comparison in self-clash mode
                    if is_self_clash and el_a.id >= el_b.id:
                        continue

                    # Check AABB overlap with tolerance
                    overlap_x = min(bb_a["max_x"], bb_b["max_x"]) - max(bb_a["min_x"], bb_b["min_x"])
                    overlap_y = min(bb_a["max_y"], bb_b["max_y"]) - max(bb_a["min_y"], bb_b["min_y"])
                    overlap_z = min(bb_a["max_z"], bb_b["max_z"]) - max(bb_a["min_z"], bb_b["min_z"])

                    if overlap_x > -tolerance and overlap_y > -tolerance and overlap_z > -tolerance:
                        # Calculate overlap distance (minimum overlap across axes)
                        dist = min(
                            max(overlap_x, 0),
                            max(overlap_y, 0),
                            max(overlap_z, 0),
                        )

                        # Classify severity by overlap distance
                        if dist > 0.1:
                            sev = ClashSeverity.CRITICAL
                            critical += 1
                        elif dist > 0.05:
                            sev = ClashSeverity.MAJOR
                            major += 1
                        elif dist > tolerance:
                            sev = ClashSeverity.MINOR
                            minor += 1
                        else:
                            sev = ClashSeverity.INFO

                        # Clash point = midpoint of overlap region
                        cx = (max(bb_a["min_x"], bb_b["min_x"]) + min(bb_a["max_x"], bb_b["max_x"])) / 2
                        cy = (max(bb_a["min_y"], bb_b["min_y"]) + min(bb_a["max_y"], bb_b["max_y"])) / 2
                        cz = (max(bb_a["min_z"], bb_b["min_z"]) + min(bb_a["max_z"], bb_b["max_z"])) / 2

                        desc = (
                            f"{el_a.ifc_type} '{el_a.name or el_a.global_id}' clashes with "
                            f"{el_b.ifc_type} '{el_b.name or el_b.global_id}' "
                            f"(overlap: {dist:.3f}m)"
                        )

                        result = ClashResult(
                            clash_test_id=test_id,
                            company_id=self.company_id,
                            sequence_name=_next_seq(self.db, ClashResult, self.company_id, *SEQ_CLASH_RESULT),
                            element_a_id=el_a.global_id,
                            element_a_name=el_a.name,
                            element_a_type=el_a.ifc_type,
                            element_b_id=el_b.global_id,
                            element_b_name=el_b.name,
                            element_b_type=el_b.ifc_type,
                            severity=sev,
                            status=ClashStatus.NEW,
                            clash_point=json.dumps({"x": round(cx, 4), "y": round(cy, 4), "z": round(cz, 4)}),
                            distance=round(dist, 4),
                            description=desc,
                            created_by=self.user_id,
                        )
                        self.db.add(result)
                        clash_count += 1

                        # Safety limit
                        if clash_count >= 5000:
                            break
                if clash_count >= 5000:
                    break

            elapsed = time.time() - start_time

            test.status = ClashTestStatus.COMPLETED
            test.total_clashes = clash_count
            test.critical_count = critical
            test.major_count = major
            test.minor_count = minor
            test.duration_seconds = round(elapsed, 2)

        except Exception as e:
            test.status = ClashTestStatus.FAILED
            test.duration_seconds = round(time.time() - start_time, 2)
            logger.error(f"Clash test {test_id} failed: {e}")

        test.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(test)
        return test

    # ─── Clash Result CRUD ───────────────────────────────────────────────

    def list_clash_results(
        self,
        clash_test_id: int,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        page_size = min(page_size, 200)
        query = (
            self.db.query(ClashResult)
            .filter(ClashResult.clash_test_id == clash_test_id, ClashResult.company_id == self.company_id)
        )
        if status:
            query = query.filter(ClashResult.status == status)
        if severity:
            query = query.filter(ClashResult.severity == severity)

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(ClashResult.severity, ClashResult.id).offset(skip).limit(page_size).all()

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_clash_result(self, result_id: int) -> Optional[ClashResult]:
        return (
            self.db.query(ClashResult)
            .filter(ClashResult.id == result_id, ClashResult.company_id == self.company_id)
            .first()
        )

    def update_clash_result(self, result_id: int, data: ClashResultUpdate) -> Optional[ClashResult]:
        result = self.get_clash_result(result_id)
        if not result:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(result, key, value)
        result.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(result)
        return result

    def resolve_clash(self, result_id: int, data: ClashResultResolve) -> Optional[ClashResult]:
        result = self.get_clash_result(result_id)
        if not result:
            return None

        result.status = ClashStatus.RESOLVED
        result.resolved_by = self.user_id
        result.resolved_date = date.today()
        result.resolution_notes = data.resolution_notes
        result.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(result)
        return result

    def assign_clash(self, result_id: int, data: ClashResultAssign) -> Optional[ClashResult]:
        result = self.get_clash_result(result_id)
        if not result:
            return None

        result.assigned_to = data.assigned_to
        if result.status == ClashStatus.NEW:
            result.status = ClashStatus.ACTIVE
        result.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(result)
        return result

    def ignore_clash(self, result_id: int) -> Optional[ClashResult]:
        result = self.get_clash_result(result_id)
        if not result:
            return None

        result.status = ClashStatus.IGNORED
        result.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(result)
        return result

    # ─── Element Search ──────────────────────────────────────────────────

    def search_elements(
        self,
        model_id: int,
        ifc_type: Optional[str] = None,
        name: Optional[str] = None,
        level: Optional[str] = None,
        material: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        page_size = min(page_size, 200)
        query = (
            self.db.query(BIMElement)
            .filter(BIMElement.model_id == model_id, BIMElement.company_id == self.company_id)
        )

        if ifc_type:
            query = query.filter(BIMElement.ifc_type == ifc_type)
        if name:
            query = query.filter(BIMElement.name.ilike(f"%{name}%"))
        if level:
            query = query.filter(BIMElement.level == level)
        if material:
            query = query.filter(BIMElement.material.ilike(f"%{material}%"))

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(BIMElement.ifc_type, BIMElement.id).offset(skip).limit(page_size).all()

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_model_summary(self, model_id: int) -> Optional[dict]:
        """Get aggregated element counts by type, level, material, discipline."""
        model = self.get_model(model_id)
        if not model:
            return None
        return self._get_model_summary_dict(model_id)

    def _get_model_summary_dict(self, model_id: int) -> dict:
        base_q = self.db.query(BIMElement).filter(BIMElement.model_id == model_id)
        total = base_q.count()

        # Group by ifc_type
        types = dict(
            self.db.query(BIMElement.ifc_type, func.count(BIMElement.id))
            .filter(BIMElement.model_id == model_id)
            .group_by(BIMElement.ifc_type)
            .all()
        )

        # Group by level
        levels = dict(
            self.db.query(BIMElement.level, func.count(BIMElement.id))
            .filter(BIMElement.model_id == model_id, BIMElement.level.isnot(None))
            .group_by(BIMElement.level)
            .all()
        )

        # Group by material
        materials = dict(
            self.db.query(BIMElement.material, func.count(BIMElement.id))
            .filter(BIMElement.model_id == model_id, BIMElement.material.isnot(None))
            .group_by(BIMElement.material)
            .all()
        )

        # Group by discipline
        disciplines = dict(
            self.db.query(BIMElement.discipline, func.count(BIMElement.id))
            .filter(BIMElement.model_id == model_id, BIMElement.discipline.isnot(None))
            .group_by(BIMElement.discipline)
            .all()
        )

        return {
            "model_id": model_id,
            "element_count": total,
            "types": types,
            "levels": levels,
            "materials": materials,
            "disciplines": disciplines,
        }
