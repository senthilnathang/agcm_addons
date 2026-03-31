"""Safety service - business logic for checklists, inspections, punch list, incidents"""

import logging
import re
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from addons.agcm_safety.models.checklist import ChecklistTemplate, ChecklistTemplateItem
from addons.agcm_safety.models.inspection import SafetyInspection as Inspection, SafetyInspectionItem as InspectionItem
from addons.agcm_safety.models.punch_list import PunchListItem
from addons.agcm_safety.models.incident import IncidentReport
from addons.agcm_safety.schemas.checklist import ChecklistTemplateCreate, ChecklistTemplateUpdate
from addons.agcm_safety.schemas.inspection import InspectionCreate, InspectionUpdate
from addons.agcm_safety.schemas.punch_list import PunchListItemCreate, PunchListItemUpdate
from addons.agcm_safety.schemas.incident import IncidentReportCreate, IncidentReportUpdate

logger = logging.getLogger(__name__)

SEQUENCE_CONFIGS = {
    "agcm_inspections_v2": ("INSP", 5),
    "agcm_punch_list_items": ("PL", 5),
    "agcm_incident_reports": ("INC", 5),
}


def _next_sequence(db: Session, model_class, company_id: int) -> str:
    """Generate next sequence for a model."""
    tablename = model_class.__tablename__
    config = SEQUENCE_CONFIGS.get(tablename)
    if not config:
        return None
    prefix, padding = config
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


class SafetyService:
    """Handles CRUD and business logic for all safety entities."""

    def __init__(self, db: Session, company_id: int, user_id: int):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id

    # =========================================================================
    # CHECKLIST TEMPLATES
    # =========================================================================

    def list_templates(
        self,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        page_size = min(page_size, 200)
        query = self.db.query(ChecklistTemplate).filter(
            ChecklistTemplate.company_id == self.company_id
        )
        if category:
            query = query.filter(ChecklistTemplate.category == category)
        if is_active is not None:
            query = query.filter(ChecklistTemplate.is_active == is_active)
        if search:
            term = f"%{search}%"
            query = query.filter(ChecklistTemplate.name.ilike(term))

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(ChecklistTemplate.id.desc()).offset(skip).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_template(self, template_id: int) -> Optional[ChecklistTemplate]:
        return (
            self.db.query(ChecklistTemplate)
            .filter(ChecklistTemplate.id == template_id, ChecklistTemplate.company_id == self.company_id)
            .first()
        )

    def get_template_detail(self, template_id: int) -> Optional[dict]:
        tpl = self.get_template(template_id)
        if not tpl:
            return None
        items = (
            self.db.query(ChecklistTemplateItem)
            .filter(ChecklistTemplateItem.template_id == template_id)
            .order_by(ChecklistTemplateItem.display_order)
            .all()
        )
        item_dicts = [
            {
                "id": i.id,
                "template_id": i.template_id,
                "description": i.description,
                "required": i.required,
                "display_order": i.display_order,
                "company_id": i.company_id,
                "created_at": i.created_at,
                "updated_at": i.updated_at,
            }
            for i in items
        ]
        return {
            **{c.key: getattr(tpl, c.key) for c in tpl.__table__.columns},
            "items": item_dicts,
        }

    def create_template(self, data: ChecklistTemplateCreate) -> ChecklistTemplate:
        tpl = ChecklistTemplate(
            company_id=self.company_id,
            name=data.name,
            description=data.description,
            category=data.category,
            is_active=data.is_active if data.is_active is not None else True,
            created_by=self.user_id,
        )
        self.db.add(tpl)
        self.db.flush()

        if data.items:
            for idx, item_data in enumerate(data.items):
                item = ChecklistTemplateItem(
                    template_id=tpl.id,
                    company_id=self.company_id,
                    description=item_data.description,
                    required=item_data.required if item_data.required is not None else True,
                    display_order=item_data.display_order if item_data.display_order else idx,
                )
                self.db.add(item)

        self.db.commit()
        self.db.refresh(tpl)
        return tpl

    def update_template(self, template_id: int, data: ChecklistTemplateUpdate) -> Optional[ChecklistTemplate]:
        tpl = self.get_template(template_id)
        if not tpl:
            return None

        update_data = data.model_dump(exclude_unset=True)
        items_data = update_data.pop("items", None)

        for key, value in update_data.items():
            setattr(tpl, key, value)
        tpl.updated_by = self.user_id

        if items_data is not None:
            self.db.query(ChecklistTemplateItem).filter(
                ChecklistTemplateItem.template_id == template_id
            ).delete()
            for idx, item_data in enumerate(items_data):
                item = ChecklistTemplateItem(
                    template_id=template_id,
                    company_id=self.company_id,
                    description=item_data.get("description", ""),
                    required=item_data.get("required", True),
                    display_order=item_data.get("display_order", idx),
                )
                self.db.add(item)

        self.db.commit()
        self.db.refresh(tpl)
        return tpl

    def delete_template(self, template_id: int) -> bool:
        tpl = self.get_template(template_id)
        if not tpl:
            return False
        self.db.delete(tpl)
        self.db.commit()
        return True

    # =========================================================================
    # INSPECTIONS
    # =========================================================================

    def list_inspections(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        page_size = min(page_size, 200)
        query = self.db.query(Inspection).filter(Inspection.company_id == self.company_id)
        if project_id:
            query = query.filter(Inspection.project_id == project_id)
        if status:
            query = query.filter(Inspection.status == status)
        if search:
            term = f"%{search}%"
            query = query.filter(
                (Inspection.inspector_name.ilike(term))
                | (Inspection.sequence_name.ilike(term))
                | (Inspection.inspection_type.ilike(term))
            )

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(Inspection.id.desc()).offset(skip).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_inspection(self, inspection_id: int) -> Optional[Inspection]:
        return (
            self.db.query(Inspection)
            .filter(Inspection.id == inspection_id, Inspection.company_id == self.company_id)
            .first()
        )

    def get_inspection_detail(self, inspection_id: int) -> Optional[dict]:
        insp = self.get_inspection(inspection_id)
        if not insp:
            return None
        items = (
            self.db.query(InspectionItem)
            .filter(InspectionItem.inspection_id == inspection_id)
            .order_by(InspectionItem.display_order)
            .all()
        )
        item_dicts = [
            {
                "id": i.id,
                "inspection_id": i.inspection_id,
                "description": i.description,
                "result": i.result,
                "notes": i.notes,
                "photo_url": i.photo_url,
                "display_order": i.display_order,
                "company_id": i.company_id,
                "created_at": i.created_at,
                "updated_at": i.updated_at,
            }
            for i in items
        ]
        return {
            **{c.key: getattr(insp, c.key) for c in insp.__table__.columns},
            "items": item_dicts,
        }

    def create_inspection(self, data: InspectionCreate) -> Inspection:
        insp = Inspection(
            company_id=self.company_id,
            sequence_name=_next_sequence(self.db, Inspection, self.company_id),
            project_id=data.project_id,
            template_id=data.template_id,
            inspector_name=data.inspector_name,
            inspector_company=data.inspector_company,
            inspection_type=data.inspection_type,
            status="scheduled",
            scheduled_date=data.scheduled_date,
            location=data.location,
            notes=data.notes,
            created_by=self.user_id,
        )
        self.db.add(insp)
        self.db.flush()

        if data.items:
            for idx, item_data in enumerate(data.items):
                item = InspectionItem(
                    inspection_id=insp.id,
                    company_id=self.company_id,
                    description=item_data.description,
                    result=item_data.result,
                    notes=item_data.notes,
                    photo_url=item_data.photo_url,
                    display_order=item_data.display_order if item_data.display_order else idx,
                )
                self.db.add(item)

        self.db.commit()
        self.db.refresh(insp)
        return insp

    def create_inspection_from_template(self, project_id: int, template_id: int, data: InspectionCreate) -> Optional[Inspection]:
        """Create an inspection pre-populated from a checklist template."""
        tpl = self.get_template(template_id)
        if not tpl:
            return None

        insp = Inspection(
            company_id=self.company_id,
            sequence_name=_next_sequence(self.db, Inspection, self.company_id),
            project_id=project_id,
            template_id=template_id,
            inspector_name=data.inspector_name,
            inspector_company=data.inspector_company,
            inspection_type=data.inspection_type or tpl.category,
            status="scheduled",
            scheduled_date=data.scheduled_date,
            location=data.location,
            notes=data.notes,
            created_by=self.user_id,
        )
        self.db.add(insp)
        self.db.flush()

        # Copy template items as inspection items
        tpl_items = (
            self.db.query(ChecklistTemplateItem)
            .filter(ChecklistTemplateItem.template_id == template_id)
            .order_by(ChecklistTemplateItem.display_order)
            .all()
        )
        for ti in tpl_items:
            item = InspectionItem(
                inspection_id=insp.id,
                company_id=self.company_id,
                description=ti.description,
                display_order=ti.display_order,
            )
            self.db.add(item)

        self.db.commit()
        self.db.refresh(insp)
        return insp

    def update_inspection(self, inspection_id: int, data: InspectionUpdate) -> Optional[Inspection]:
        insp = self.get_inspection(inspection_id)
        if not insp:
            return None

        update_data = data.model_dump(exclude_unset=True)
        items_data = update_data.pop("items", None)

        for key, value in update_data.items():
            setattr(insp, key, value)
        insp.updated_by = self.user_id

        if items_data is not None:
            self.db.query(InspectionItem).filter(
                InspectionItem.inspection_id == inspection_id
            ).delete()
            for idx, item_data in enumerate(items_data):
                item = InspectionItem(
                    inspection_id=inspection_id,
                    company_id=self.company_id,
                    description=item_data.get("description", ""),
                    result=item_data.get("result"),
                    notes=item_data.get("notes"),
                    photo_url=item_data.get("photo_url"),
                    display_order=item_data.get("display_order", idx),
                )
                self.db.add(item)

        self.db.commit()
        self.db.refresh(insp)
        return insp

    def start_inspection(self, inspection_id: int) -> Optional[Inspection]:
        insp = self.get_inspection(inspection_id)
        if not insp:
            return None
        insp.status = "in_progress"
        insp.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(insp)
        return insp

    def complete_inspection(self, inspection_id: int, overall_result: str) -> Optional[Inspection]:
        insp = self.get_inspection(inspection_id)
        if not insp:
            return None
        insp.status = "passed" if overall_result == "pass" else ("failed" if overall_result == "fail" else "conditional")
        insp.overall_result = overall_result
        insp.completed_date = date.today()
        insp.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(insp)
        return insp

    def delete_inspection(self, inspection_id: int) -> bool:
        insp = self.get_inspection(inspection_id)
        if not insp:
            return False
        self.db.delete(insp)
        self.db.commit()
        return True

    # =========================================================================
    # PUNCH LIST
    # =========================================================================

    def list_punch_items(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        page_size = min(page_size, 200)
        query = self.db.query(PunchListItem).filter(PunchListItem.company_id == self.company_id)
        if project_id:
            query = query.filter(PunchListItem.project_id == project_id)
        if status:
            query = query.filter(PunchListItem.status == status)
        if priority:
            query = query.filter(PunchListItem.priority == priority)
        if search:
            term = f"%{search}%"
            query = query.filter(
                (PunchListItem.title.ilike(term))
                | (PunchListItem.sequence_name.ilike(term))
            )

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(PunchListItem.id.desc()).offset(skip).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_punch_item(self, item_id: int) -> Optional[PunchListItem]:
        return (
            self.db.query(PunchListItem)
            .filter(PunchListItem.id == item_id, PunchListItem.company_id == self.company_id)
            .first()
        )

    def create_punch_item(self, data: PunchListItemCreate) -> PunchListItem:
        item = PunchListItem(
            company_id=self.company_id,
            sequence_name=_next_sequence(self.db, PunchListItem, self.company_id),
            project_id=data.project_id,
            title=data.title,
            description=data.description,
            status="open",
            priority=data.priority or "medium",
            location=data.location,
            trade=data.trade,
            assigned_to=data.assigned_to,
            due_date=data.due_date,
            photo_before_url=data.photo_before_url,
            notes=data.notes,
            created_by=self.user_id,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_punch_item(self, item_id: int, data: PunchListItemUpdate) -> Optional[PunchListItem]:
        item = self.get_punch_item(item_id)
        if not item:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)
        item.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(item)
        return item

    def assign_punch_item(self, item_id: int, assigned_to: int) -> Optional[PunchListItem]:
        item = self.get_punch_item(item_id)
        if not item:
            return None
        item.assigned_to = assigned_to
        if item.status == "open":
            item.status = "in_progress"
        item.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(item)
        return item

    def complete_punch_item(self, item_id: int) -> Optional[PunchListItem]:
        item = self.get_punch_item(item_id)
        if not item:
            return None
        item.status = "completed"
        item.completed_date = date.today()
        item.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(item)
        return item

    def verify_punch_item(self, item_id: int) -> Optional[PunchListItem]:
        item = self.get_punch_item(item_id)
        if not item:
            return None
        item.status = "verified"
        item.verified_date = date.today()
        item.verified_by = self.user_id
        item.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_punch_item(self, item_id: int) -> bool:
        item = self.get_punch_item(item_id)
        if not item:
            return False
        self.db.delete(item)
        self.db.commit()
        return True

    # =========================================================================
    # INCIDENT REPORTS
    # =========================================================================

    def list_incidents(
        self,
        project_id: Optional[int] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        page_size = min(page_size, 200)
        query = self.db.query(IncidentReport).filter(IncidentReport.company_id == self.company_id)
        if project_id:
            query = query.filter(IncidentReport.project_id == project_id)
        if severity:
            query = query.filter(IncidentReport.severity == severity)
        if status:
            query = query.filter(IncidentReport.status == status)
        if search:
            term = f"%{search}%"
            query = query.filter(
                (IncidentReport.title.ilike(term))
                | (IncidentReport.sequence_name.ilike(term))
            )

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(IncidentReport.id.desc()).offset(skip).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_incident(self, incident_id: int) -> Optional[IncidentReport]:
        return (
            self.db.query(IncidentReport)
            .filter(IncidentReport.id == incident_id, IncidentReport.company_id == self.company_id)
            .first()
        )

    def create_incident(self, data: IncidentReportCreate) -> IncidentReport:
        incident = IncidentReport(
            company_id=self.company_id,
            sequence_name=_next_sequence(self.db, IncidentReport, self.company_id),
            project_id=data.project_id,
            title=data.title,
            description=data.description,
            severity=data.severity,
            status="reported",
            incident_date=data.incident_date,
            incident_time=data.incident_time,
            location=data.location,
            injured_party=data.injured_party,
            injury_description=data.injury_description,
            witness_names=data.witness_names,
            osha_recordable=data.osha_recordable or False,
            photo_urls=data.photo_urls,
            notes=data.notes,
            reported_by=self.user_id,
            created_by=self.user_id,
        )
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def update_incident(self, incident_id: int, data: IncidentReportUpdate) -> Optional[IncidentReport]:
        incident = self.get_incident(incident_id)
        if not incident:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(incident, key, value)
        incident.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(incident)
        return incident

    def investigate_incident(self, incident_id: int, root_cause: str, corrective_action: str) -> Optional[IncidentReport]:
        incident = self.get_incident(incident_id)
        if not incident:
            return None
        incident.status = "investigating"
        incident.investigated_by = self.user_id
        incident.investigation_date = date.today()
        incident.root_cause = root_cause
        incident.corrective_action = corrective_action
        incident.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def close_incident(self, incident_id: int, days_lost: int = 0) -> Optional[IncidentReport]:
        incident = self.get_incident(incident_id)
        if not incident:
            return None
        incident.status = "closed"
        incident.closed_date = date.today()
        incident.days_lost = days_lost
        incident.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def delete_incident(self, incident_id: int) -> bool:
        incident = self.get_incident(incident_id)
        if not incident:
            return False
        self.db.delete(incident)
        self.db.commit()
        return True
