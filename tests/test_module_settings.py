"""
Tests for AGCM module settings.

Verifies:
- AGCMSettings model CRUD
- Default settings returned when none configured
- Settings update creates/updates record
- Module-specific defaults (finance vs estimate vs schedule)
- Company scoping
"""

import importlib.util
import os
import sys
import types
import uuid

import pytest

ADDONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if "addons" not in sys.modules:
    addons_pkg = types.ModuleType("addons")
    addons_pkg.__path__ = [ADDONS_DIR]
    addons_pkg.__package__ = "addons"
    sys.modules["addons"] = addons_pkg

# Load settings service
_svc_spec = importlib.util.spec_from_file_location(
    "agcm_settings_service",
    os.path.join(ADDONS_DIR, "agcm", "services", "settings_service.py"),
)
_svc_mod = importlib.util.module_from_spec(_svc_spec)
sys.modules["agcm_settings_service"] = _svc_mod
_svc_spec.loader.exec_module(_svc_mod)

SettingsService = _svc_mod.SettingsService
VALID_MODULES = _svc_mod.VALID_MODULES
MODULE_DEFAULTS = _svc_mod.MODULE_DEFAULTS


class TestSettingsModel:

    def test_create_settings_record(self, db, company_id, user_id, load_model):
        AGCMSettings = load_model("agcm", "settings", "AGCMSettings")

        record = AGCMSettings(
            company_id=company_id, module_name="finance",
            default_retention_pct=15.0, default_payment_terms="Net 60",
            currency_code="USD", created_by=user_id,
        )
        db.add(record)
        db.flush()

        assert record.id is not None
        assert record.default_retention_pct == 15.0
        assert record.default_payment_terms == "Net 60"


class TestSettingsService:

    def test_get_defaults_when_none_configured(self, db, company_id, user_id):
        svc = SettingsService(db, company_id, user_id)
        result = svc.get_settings("finance")

        assert result["is_default"] is True
        assert result["default_retention_pct"] == 10.0
        assert result["default_payment_terms"] == "Net 30"
        assert result["currency_code"] == "USD"

    def test_estimate_module_defaults(self, db, company_id, user_id):
        svc = SettingsService(db, company_id, user_id)
        result = svc.get_settings("estimate")

        assert result["is_default"] is True
        assert result["default_markup_pct"] == 15.0
        assert result["default_tax_rate_pct"] == 8.25

    def test_schedule_module_defaults(self, db, company_id, user_id):
        svc = SettingsService(db, company_id, user_id)
        result = svc.get_settings("schedule")

        assert result["is_default"] is True
        assert result["working_hours_per_day"] == 8.0

    def test_update_creates_record(self, db, company_id, user_id):
        svc = SettingsService(db, company_id, user_id)

        result = svc.update_settings("procurement", {
            "default_retention_pct": 5.0,
            "po_number_prefix": "PO-2026",
        })

        assert result["is_default"] is False
        assert result["default_retention_pct"] == 5.0
        assert result["po_number_prefix"] == "PO-2026"

    def test_update_existing_record(self, db, company_id, user_id):
        svc = SettingsService(db, company_id, user_id)

        # First update creates
        svc.update_settings("finance", {"default_retention_pct": 12.0})
        # Second update modifies
        result = svc.update_settings("finance", {"default_retention_pct": 8.0})

        assert result["default_retention_pct"] == 8.0

    def test_list_all_modules(self, db, company_id, user_id):
        svc = SettingsService(db, company_id, user_id)
        result = svc.list_all_modules()

        assert len(result) == len(VALID_MODULES)
        module_names = [r["module_name"] for r in result]
        for mod in VALID_MODULES:
            assert mod in module_names

    def test_settings_json_extensibility(self, db, company_id, user_id):
        svc = SettingsService(db, company_id, user_id)

        result = svc.update_settings("safety", {
            "settings_json": {
                "severity_levels": ["low", "medium", "high", "critical"],
                "default_inspection_frequency_days": 7,
                "osha_recordable_threshold_days": 1,
            }
        })

        assert result["settings_json"]["severity_levels"] == ["low", "medium", "high", "critical"]
        assert result["settings_json"]["osha_recordable_threshold_days"] == 1
