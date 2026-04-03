"""AGCM Settings Service — get/update per-module company settings."""

import logging
from typing import Dict, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

VALID_MODULES = [
    "finance", "procurement", "estimate", "schedule",
    "safety", "resource", "document", "reporting",
    "portal", "bim", "general",
]

# Default settings per module
MODULE_DEFAULTS = {
    "finance": {
        "default_retention_pct": 10.0,
        "default_tax_rate_pct": 0,
        "default_payment_terms": "Net 30",
        "invoice_number_prefix": "INV",
        "currency_code": "USD",
    },
    "procurement": {
        "default_retention_pct": 10.0,
        "default_payment_terms": "Net 30",
        "po_number_prefix": "PO",
    },
    "estimate": {
        "default_markup_pct": 15.0,
        "default_tax_rate_pct": 8.25,
    },
    "schedule": {
        "working_hours_per_day": 8.0,
    },
    "resource": {
        "overtime_multiplier": 1.5,
        "working_hours_per_day": 8.0,
    },
    "general": {
        "currency_code": "USD",
        "default_retention_pct": 10.0,
    },
}


def _get_model():
    import sys
    mod = sys.modules.get("agcm_settings")
    if mod:
        return mod.AGCMSettings
    from addons.agcm.models.settings import AGCMSettings
    return AGCMSettings


class SettingsService:
    def __init__(self, db: Session, company_id: int, user_id: int):
        self.db = db
        self.company_id = company_id
        self.user_id = user_id

    def get_settings(self, module_name: str) -> dict:
        """Get settings for a module. Returns defaults if none configured."""
        AGCMSettings = _get_model()
        record = (
            self.db.query(AGCMSettings)
            .filter(
                AGCMSettings.company_id == self.company_id,
                AGCMSettings.module_name == module_name,
            )
            .first()
        )

        defaults = MODULE_DEFAULTS.get(module_name, {})

        if not record:
            return {
                "module_name": module_name,
                "company_id": self.company_id,
                "is_default": True,
                **{
                    "default_retention_pct": defaults.get("default_retention_pct", 10.0),
                    "default_markup_pct": defaults.get("default_markup_pct", 0),
                    "default_tax_rate_pct": defaults.get("default_tax_rate_pct", 0),
                    "default_payment_terms": defaults.get("default_payment_terms", "Net 30"),
                    "po_number_prefix": defaults.get("po_number_prefix", "PO"),
                    "invoice_number_prefix": defaults.get("invoice_number_prefix", "INV"),
                    "currency_code": defaults.get("currency_code", "USD"),
                    "working_hours_per_day": defaults.get("working_hours_per_day", 8.0),
                    "overtime_multiplier": defaults.get("overtime_multiplier", 1.5),
                    "settings_json": {},
                },
            }

        return {
            "id": record.id,
            "module_name": record.module_name,
            "company_id": record.company_id,
            "is_default": False,
            "default_retention_pct": record.default_retention_pct,
            "default_markup_pct": record.default_markup_pct,
            "default_tax_rate_pct": record.default_tax_rate_pct,
            "default_payment_terms": record.default_payment_terms,
            "po_number_prefix": record.po_number_prefix,
            "invoice_number_prefix": record.invoice_number_prefix,
            "currency_code": record.currency_code,
            "working_hours_per_day": record.working_hours_per_day,
            "overtime_multiplier": record.overtime_multiplier,
            "settings_json": record.settings_json or {},
        }

    def update_settings(self, module_name: str, data: dict) -> dict:
        """Update settings for a module. Creates record if none exists."""
        AGCMSettings = _get_model()
        record = (
            self.db.query(AGCMSettings)
            .filter(
                AGCMSettings.company_id == self.company_id,
                AGCMSettings.module_name == module_name,
            )
            .first()
        )

        allowed_fields = {
            "default_retention_pct", "default_markup_pct", "default_tax_rate_pct",
            "default_payment_terms", "po_number_prefix", "invoice_number_prefix",
            "currency_code", "working_hours_per_day", "overtime_multiplier",
            "settings_json", "notes",
        }

        if not record:
            record = AGCMSettings(
                company_id=self.company_id,
                module_name=module_name,
                created_by=self.user_id,
            )
            self.db.add(record)

        for key, value in data.items():
            if key in allowed_fields and value is not None:
                setattr(record, key, value)
        record.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(record)
        return self.get_settings(module_name)

    def list_all_modules(self) -> list:
        """List all module settings (configured + defaults for unconfigured)."""
        AGCMSettings = _get_model()
        configured = (
            self.db.query(AGCMSettings)
            .filter(AGCMSettings.company_id == self.company_id)
            .all()
        )
        configured_modules = {r.module_name for r in configured}

        result = []
        for mod in VALID_MODULES:
            result.append(self.get_settings(mod))
        return result
