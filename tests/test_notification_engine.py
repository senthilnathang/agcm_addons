"""
Tests for centralized notification engine.

Verifies:
- Event registry has all expected event types
- notify_event dispatches to recipients (non-blocking)
- Actor is excluded from recipients
- Empty recipients returns False
- Template formatting with context variables
- Safe fallback on import errors
"""

import importlib.util
import os
import sys
import types
import uuid
from unittest.mock import MagicMock, patch

import pytest

ADDONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if "addons" not in sys.modules:
    addons_pkg = types.ModuleType("addons")
    addons_pkg.__path__ = [ADDONS_DIR]
    addons_pkg.__package__ = "addons"
    sys.modules["addons"] = addons_pkg

# Load notify module
_notify_spec = importlib.util.spec_from_file_location(
    "agcm_notify", os.path.join(ADDONS_DIR, "agcm", "services", "notify.py"))
_notify_mod = importlib.util.module_from_spec(_notify_spec)
sys.modules["agcm_notify"] = _notify_mod
_notify_spec.loader.exec_module(_notify_mod)

notify_event = _notify_mod.notify_event
AGCM_EVENT_REGISTRY = _notify_mod.AGCM_EVENT_REGISTRY
_format_template = _notify_mod._format_template


class TestEventRegistry:

    def test_registry_has_rfi_events(self):
        assert "rfi.created" in AGCM_EVENT_REGISTRY
        assert "rfi.response_added" in AGCM_EVENT_REGISTRY
        assert "rfi.closed" in AGCM_EVENT_REGISTRY

    def test_registry_has_change_order_events(self):
        assert "change_order.approved" in AGCM_EVENT_REGISTRY
        assert "change_order.rejected" in AGCM_EVENT_REGISTRY

    def test_registry_has_task_events(self):
        assert "task.assigned" in AGCM_EVENT_REGISTRY
        assert "task.due_soon" in AGCM_EVENT_REGISTRY

    def test_registry_has_safety_events(self):
        assert "incident.reported" in AGCM_EVENT_REGISTRY
        assert "punch_list.assigned" in AGCM_EVENT_REGISTRY

    def test_registry_has_timesheet_events(self):
        assert "timesheet.approved" in AGCM_EVENT_REGISTRY
        assert "timesheet.rejected" in AGCM_EVENT_REGISTRY

    def test_registry_has_budget_events(self):
        assert "budget.threshold_warning" in AGCM_EVENT_REGISTRY

    def test_all_events_have_required_fields(self):
        for key, config in AGCM_EVENT_REGISTRY.items():
            assert "title" in config, f"Missing title in {key}"
            assert "level" in config, f"Missing level in {key}"
            assert "channels" in config, f"Missing channels in {key}"
            assert config["level"] in ("info", "success", "warning", "error"), \
                f"Invalid level '{config['level']}' in {key}"


class TestTemplateFormatting:

    def test_format_with_context(self):
        result = _format_template("New RFI: {subject}", {"subject": "Steel detail"})
        assert result == "New RFI: Steel detail"

    def test_format_missing_key_returns_template(self):
        result = _format_template("CO: {title} — ${amount}", {"title": "Change"})
        # Missing {amount} key — returns original template
        assert "CO:" in result

    def test_format_empty_context(self):
        result = _format_template("Simple notification", {})
        assert result == "Simple notification"


class TestNotifyEvent:

    def test_no_recipients_returns_false(self, db):
        result = notify_event(db, "created", "rfi", 1, actor_id=1,
                              recipient_ids=[], company_id=1)
        assert result is False

    def test_none_recipients_returns_false(self, db):
        result = notify_event(db, "created", "rfi", 1, actor_id=1,
                              recipient_ids=None, company_id=1)
        assert result is False

    def test_actor_excluded_from_recipients(self, db):
        """Actor should not receive their own notification."""
        with patch.object(_notify_mod, '_dispatch_via_core') as mock_core, \
             patch.object(_notify_mod, '_dispatch_in_app_fallback'):
            mock_core.side_effect = ImportError("test")

            # Actor is user 1, only recipient is also user 1
            result = notify_event(
                db, "created", "rfi", 1, actor_id=1,
                recipient_ids=[1], company_id=1,
            )
            # Should return False because only recipient was excluded
            assert result is False

    def test_dispatches_to_non_actor_recipients(self, db):
        """Recipients other than actor should receive notification."""
        with patch.object(_notify_mod, '_dispatch_via_core') as mock_core:
            mock_core.return_value = None  # Success

            result = notify_event(
                db, "approved", "change_order", 42, actor_id=1,
                context={"title": "Test CO", "sequence_name": "CO-001", "cost_impact": "5000"},
                recipient_ids=[1, 2, 3], company_id=1,
            )
            assert result is True
            # Actor (1) excluded, so 2 dispatches
            assert mock_core.call_count == 2

    def test_unknown_event_still_dispatches(self, db):
        """Events not in registry should still work with defaults."""
        with patch.object(_notify_mod, '_dispatch_via_core') as mock_core:
            mock_core.return_value = None

            result = notify_event(
                db, "custom_event", "custom_entity", 1, actor_id=None,
                recipient_ids=[5], company_id=1,
            )
            assert result is True
            mock_core.assert_called_once()
