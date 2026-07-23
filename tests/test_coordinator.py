"""Tests for missing checks, aggregation, ignores, signatures, and events."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.template_entity_checker import coordinator as coordinator_module
from custom_components.template_entity_checker.coordinator import (
    TemplateEntityCheckerCoordinator,
    _configured_ignored_entities,
    _fire_result_changed_event,
    _missing_entity_findings,
    _partition_ignored,
    _result_signature,
)
from custom_components.template_entity_checker.models import (
    SourceLoadError,
    StaticReference,
    TemplateSource,
)


class Lookup:
    def __init__(self, values=()):
        self.values = set(values)

    def get(self, key):
        return object() if key in self.values else None

    async_get = get


def source():
    return TemplateSource(
        source_id="helper-id",
        helper="Average humidity",
        template_type="sensor",
        template_field="state",
        template="",
    )


def reference(entity_id, line=1):
    return StaticReference(
        entity_id=entity_id,
        reference=f"states('{entity_id}')",
        line=line,
        column=4,
    )


def test_missing_only_when_absent_from_state_and_registry():
    refs = [(source(), reference("sensor.missing"))]
    assert "sensor.missing" in _missing_entity_findings(refs, Lookup(), Lookup())
    assert _missing_entity_findings(refs, Lookup(["sensor.missing"]), Lookup()) == {}
    assert _missing_entity_findings(refs, Lookup(), Lookup(["sensor.missing"])) == {}


def test_unknown_and_unavailable_states_are_not_missing():
    refs = [
        (source(), reference("sensor.unknown")),
        (source(), reference("sensor.unavailable")),
    ]
    assert (
        _missing_entity_findings(
            refs,
            Lookup(["sensor.unknown", "sensor.unavailable"]),
            Lookup(),
        )
        == {}
    )


def test_duplicate_findings_are_grouped_with_occurrence_count():
    refs = [
        (source(), reference("sensor.same", 1)),
        (source(), reference("sensor.same", 2)),
    ]
    findings = _missing_entity_findings(refs, Lookup(), Lookup())
    item = findings["sensor.same"][0]
    assert item["occurrence_count"] == 2
    assert item["locations"] == [
        {"line": 1, "column": 4},
        {"line": 2, "column": 4},
    ]


def test_exact_ignore_partition_is_transparent():
    detected = {"sensor.keep": [{}], "sensor.ignore": [{"helper": "x"}]}
    active, ignored = _partition_ignored(detected, {"sensor.ignore"})
    assert active == {"sensor.keep": [{}]}
    assert ignored == {"sensor.ignore": [{"helper": "x"}]}


def test_ignore_normalization_is_exact_and_deduplicated():
    assert _configured_ignored_entities(
        {"ignored_entities": " sensor.one, sensor.two\nsensor.one "}
    ) == ["sensor.one", "sensor.two"]


def test_signature_is_order_independent_for_mapping_keys():
    assert _result_signature({"sensor.b": [], "sensor.a": []}) == _result_signature(
        {"sensor.a": [], "sensor.b": []}
    )


def test_result_event_skips_baseline_and_unchanged():
    calls = []
    hass = SimpleNamespace(
        bus=SimpleNamespace(async_fire=lambda *args: calls.append(args))
    )
    missing = {"sensor.x": []}
    signature = _result_signature(missing)
    _fire_result_changed_event(hass, None, missing, signature, "now")
    _fire_result_changed_event(
        hass,
        {"complete": True, "result_signature": signature, "missing_entities": missing},
        missing,
        signature,
        "now",
    )
    assert calls == []


def test_result_event_reports_added_and_removed():
    calls = []
    hass = SimpleNamespace(
        bus=SimpleNamespace(async_fire=lambda *args: calls.append(args))
    )
    previous = {"sensor.old": []}
    current = {"sensor.new": []}
    _fire_result_changed_event(
        hass,
        {
            "complete": True,
            "result_signature": _result_signature(previous),
            "missing_entities": previous,
        },
        current,
        _result_signature(current),
        "now",
    )
    payload = calls[0][1]
    assert payload["added_entities"] == ["sensor.new"]
    assert payload["removed_entities"] == ["sensor.old"]


async def test_full_scan_separates_results_and_updates_notification(hass, monkeypatch):
    entry = MockConfigEntry(
        domain="template_entity_checker",
        data={
            "scan_interval": 15,
            "notifications": True,
            "template_types": ["sensor"],
            "ignored_entities": "sensor.ignored",
        },
    )
    scan_source = TemplateSource(
        source_id="helper-id",
        helper="Average humidity",
        template_type="sensor",
        template_field="state",
        template=(
            "{{ states('sensor.missing') }} + "
            "{{ states('sensor.ignored') }} + {{ states(variable) }}"
        ),
    )
    monkeypatch.setattr(
        coordinator_module,
        "load_template_sources",
        lambda _hass, _types: ([scan_source], []),
    )
    notifications = []
    monkeypatch.setattr(
        coordinator_module,
        "update_notification",
        lambda _hass, missing, *, enabled: notifications.append((missing, enabled)),
    )

    coordinator = TemplateEntityCheckerCoordinator(hass, entry)
    result = await coordinator._async_scan()

    assert result["status"] == "missing_entities"
    assert list(result["missing_entities"]) == ["sensor.missing"]
    assert list(result["ignored_matches"]) == ["sensor.ignored"]
    assert result["parser_diagnostics"][0]["code"] == "dynamic_entity_reference"
    assert result["load_errors"] == []
    assert result["missing_entities"]["sensor.missing"][0]["source_id"] == ("helper-id")
    assert notifications[0][1] is True

    coordinator.data = result
    notifications.clear()
    unchanged = await coordinator._async_scan()
    assert unchanged["result_signature"] == result["result_signature"]
    assert notifications == []


async def test_partial_source_failure_preserves_notification(hass, monkeypatch):
    entry = MockConfigEntry(domain="template_entity_checker", data={})
    monkeypatch.setattr(
        coordinator_module,
        "load_template_sources",
        lambda _hass, _types: (
            [],
            [SourceLoadError("broken-id", "Broken helper", "bad schema")],
        ),
    )
    notification = AsyncMock()
    monkeypatch.setattr(coordinator_module, "update_notification", notification)

    coordinator = TemplateEntityCheckerCoordinator(hass, entry)
    result = await coordinator._async_scan()

    assert result["status"] == "partial_error"
    assert result["complete"] is False
    assert result["load_errors"][0]["source_id"] == "broken-id"
    notification.assert_not_called()


async def test_start_scanning_is_idempotent(hass):
    entry = MockConfigEntry(domain="template_entity_checker", data={})
    coordinator = TemplateEntityCheckerCoordinator(hass, entry)
    coordinator.async_refresh = AsyncMock()

    await coordinator.async_start_scanning()
    await coordinator.async_start_scanning()

    coordinator.async_refresh.assert_awaited_once()
    assert coordinator.update_interval.total_seconds() == 15 * 60
