"""DailyActivityLog service - business logic for daily logs and child entities"""

import logging
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from addons.agcm.models.daily_activity_log import DailyActivityLog
from addons.agcm.models.manpower import ManPower
from addons.agcm.models.notes import Notes
from addons.agcm.models.inspection import Inspection
from addons.agcm.models.accident import Accident
from addons.agcm.models.visitor import Visitor
from addons.agcm.models.safety_violation import SafetyViolation
from addons.agcm.models.delay import Delay
from addons.agcm.models.deficiency import Deficiency
from addons.agcm.models.photo import Photo
from addons.agcm.models.weather import Weather, WeatherForecast
from addons.agcm.services.sequence_service import next_sequence

logger = logging.getLogger(__name__)


class DailyActivityLogService:
    """
    Handles DailyActivityLog CRUD and business logic.

    Migrated business rules from Odoo:
    - Auto-generates sequence_name (LOG-XXXX)
    - Date validation: must be within 6 days of today
    - "makelog" (copy): duplicates a log with selective child copying
    - Weather forecast auto-fetch on create (delegated to weather service)
    """

    def __init__(self, db: Session, company_id: int, user_id: int):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id

    def _next_sequence(self) -> str:
        """Generate next daily log sequence: DL00001, DL00002, etc."""
        return next_sequence(self.db, DailyActivityLog, self.company_id)

    def _validate_date(self, log_date: date) -> Optional[str]:
        """Validate date is within 6 days of today."""
        today = date.today()
        date_range = timedelta(days=6)
        if log_date < today - date_range or log_date > today + date_range:
            return "Date must be within 6 days before or after today."
        return None

    def list_logs(
        self,
        page: int = 1,
        page_size: int = 20,
        project_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> dict:
        """List daily logs with pagination and filtering."""
        query = self.db.query(DailyActivityLog).filter(
            DailyActivityLog.company_id == self.company_id,
        )

        if project_id:
            query = query.filter(DailyActivityLog.project_id == project_id)
        if date_from:
            query = query.filter(DailyActivityLog.date >= date_from)
        if date_to:
            query = query.filter(DailyActivityLog.date <= date_to)

        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(DailyActivityLog.date.desc()).offset(skip).limit(page_size).all()

        return {
            "items": items,
            "results": items,
            "total": total,
            "count": total,
            "page": page,
            "page_size": page_size,
        }

    def get_log(self, log_id: int) -> Optional[DailyActivityLog]:
        """Get a single daily log by ID."""
        return (
            self.db.query(DailyActivityLog)
            .filter(
                DailyActivityLog.id == log_id,
                DailyActivityLog.company_id == self.company_id,
            )
            .first()
        )

    def get_log_detail(self, log_id: int) -> Optional[dict]:
        """Get daily log with child entity counts."""
        log = self.get_log(log_id)
        if not log:
            return None

        counts = {
            "weather_count": self.db.query(func.count(Weather.id)).filter(Weather.dailylog_id == log_id).scalar() or 0,
            "weather_forecast_count": self.db.query(func.count(WeatherForecast.id)).filter(WeatherForecast.dailylog_id == log_id).scalar() or 0,
            "manpower_count": self.db.query(func.count(ManPower.id)).filter(ManPower.dailylog_id == log_id).scalar() or 0,
            "notes_count": self.db.query(func.count(Notes.id)).filter(Notes.dailylog_id == log_id).scalar() or 0,
            "inspection_count": self.db.query(func.count(Inspection.id)).filter(Inspection.dailylog_id == log_id).scalar() or 0,
            "accident_count": self.db.query(func.count(Accident.id)).filter(Accident.dailylog_id == log_id).scalar() or 0,
            "visitor_count": self.db.query(func.count(Visitor.id)).filter(Visitor.dailylog_id == log_id).scalar() or 0,
            "safety_violation_count": self.db.query(func.count(SafetyViolation.id)).filter(SafetyViolation.dailylog_id == log_id).scalar() or 0,
            "delay_count": self.db.query(func.count(Delay.id)).filter(Delay.dailylog_id == log_id).scalar() or 0,
            "deficiency_count": self.db.query(func.count(Deficiency.id)).filter(Deficiency.dailylog_id == log_id).scalar() or 0,
            "photo_count": self.db.query(func.count(Photo.id)).filter(Photo.dailylog_id == log_id).scalar() or 0,
        }

        return {
            **{c.key: getattr(log, c.key) for c in log.__table__.columns},
            **counts,
        }

    def create_log(self, project_id: int, log_date: date) -> DailyActivityLog:
        """Create a new daily activity log."""
        error = self._validate_date(log_date)
        if error:
            raise ValueError(error)

        log = DailyActivityLog(
            company_id=self.company_id,
            sequence_name=self._next_sequence(),
            date=log_date,
            project_id=project_id,
            created_by=self.user_id,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def update_log(self, log_id: int, log_date: Optional[date] = None, project_id: Optional[int] = None) -> Optional[DailyActivityLog]:
        """Update a daily log."""
        log = self.get_log(log_id)
        if not log:
            return None

        if log_date is not None:
            error = self._validate_date(log_date)
            if error:
                raise ValueError(error)
            log.date = log_date

        if project_id is not None:
            log.project_id = project_id

        log.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(log)
        return log

    def delete_log(self, log_id: int) -> bool:
        """Delete a daily log and cascade to children."""
        log = self.get_log(log_id)
        if not log:
            return False
        self.db.delete(log)
        self.db.commit()
        return True

    def makelog(
        self,
        source_log_id: int,
        target_date: Optional[date] = None,
        copy_manpower: bool = False,
        copy_safety: bool = False,
        copy_observations: bool = False,
        copy_inspections: bool = False,
        copy_delays: bool = False,
    ) -> DailyActivityLog:
        """
        Copy a daily log with selective child entity copying.

        Migrated from Odoo's DailyActivityLog.makelog().
        Creates a new log for the target date, then optionally copies
        selected child entities from the source log.
        """
        source = self.get_log(source_log_id)
        if not source:
            raise ValueError(f"Source log {source_log_id} not found")

        if target_date is None:
            target_date = date.today()

        # Create the new log
        new_log = DailyActivityLog(
            company_id=self.company_id,
            sequence_name=self._next_sequence(),
            date=target_date,
            project_id=source.project_id,
            copy_id=source.id,
            created_by=self.user_id,
        )
        self.db.add(new_log)
        self.db.flush()

        if copy_manpower:
            self._copy_children(ManPower, source.id, new_log.id)

        if copy_safety:
            self._copy_children(SafetyViolation, source.id, new_log.id)

        if copy_observations:
            self._copy_children(Notes, source.id, new_log.id)

        if copy_inspections:
            self._copy_children(Inspection, source.id, new_log.id)

        if copy_delays:
            self._copy_children(Delay, source.id, new_log.id)

        self.db.commit()
        self.db.refresh(new_log)
        return new_log

    def _copy_children(self, model_class, source_log_id: int, target_log_id: int):
        """Copy child records from source log to target log."""
        children = (
            self.db.query(model_class)
            .filter(model_class.dailylog_id == source_log_id)
            .all()
        )
        for child in children:
            # Build new record, copying all columns except id, dailylog_id, copy_id, timestamps
            skip_cols = {"id", "created_at", "updated_at", "created_by", "updated_by"}
            new_data = {}
            for col in child.__table__.columns:
                if col.key in skip_cols:
                    continue
                new_data[col.key] = getattr(child, col.key)

            new_data["dailylog_id"] = target_log_id
            new_data["copy_id"] = child.id
            new_data["created_by"] = self.user_id

            # Generate new sequence
            if hasattr(model_class, "sequence_name"):
                new_data["sequence_name"] = next_sequence(self.db, model_class, self.company_id)

            new_record = model_class(**new_data)
            self.db.add(new_record)

    # =========================================================================
    # Child entity CRUD (generic pattern for all daily log children)
    # =========================================================================

    def list_children(self, model_class, dailylog_id: int, page: int = 1, page_size: int = 50) -> dict:
        """List child entities for a daily log."""
        query = self.db.query(model_class).filter(
            model_class.dailylog_id == dailylog_id,
        )
        total = query.count()
        skip = (page - 1) * page_size
        items = query.order_by(model_class.id.desc()).offset(skip).limit(page_size).all()
        return {
            "items": items,
            "results": items,
            "total": total,
            "count": total,
            "page": page,
            "page_size": page_size,
        }

    def get_child(self, model_class, record_id: int):
        """Get a single child entity by ID."""
        return self.db.query(model_class).filter(model_class.id == record_id).first()

    def create_child(self, model_class, data: dict):
        """Create a child entity from dict data."""
        data["company_id"] = self.company_id
        data["created_by"] = self.user_id

        # Auto-generate sequence_name
        if hasattr(model_class, "sequence_name"):
            data["sequence_name"] = next_sequence(self.db, model_class, self.company_id)

        # Compute total_hours for ManPower
        if model_class is ManPower:
            workers = data.get("number_of_workers", 0) or 0
            hours = data.get("number_of_hours", 0.0) or 0.0
            data["total_hours"] = workers * hours

        record = model_class(**data)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def update_child(self, model_class, record_id: int, data: dict):
        """Update a child entity with partial data."""
        record = self.get_child(model_class, record_id)
        if not record:
            return None

        for key, value in data.items():
            setattr(record, key, value)

        record.updated_by = self.user_id

        # Recompute total_hours for ManPower
        if model_class is ManPower:
            record.compute_total_hours()

        self.db.commit()
        self.db.refresh(record)
        return record

    def delete_child(self, model_class, record_id: int) -> bool:
        """Delete a child entity."""
        record = self.get_child(model_class, record_id)
        if not record:
            return False
        self.db.delete(record)
        self.db.commit()
        return True
