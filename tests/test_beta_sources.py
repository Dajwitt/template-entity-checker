"""Confirmed November TemplateSelector fields and strict source boundaries."""

from types import SimpleNamespace

import pytest

from custom_components.template_entity_checker.template_sources import (
    _sources_from_entry,
    load_template_sources,
)

NEW_FIELDS = {
    "climate": (
        "hvac_modes",
        "hvac_mode",
        "hvac_action",
        "current_temperature",
        "target_temperature",
    ),
    "media_player": (
        "state",
        "volume_level",
        "is_volume_muted",
        "source",
        "source_list",
    ),
    "water_heater": (
        "operation_list",
        "operation_mode",
        "current_temperature",
        "target_temperature",
    ),
}


def entry(kind, **overrides):
    options = {field: "{{ states('sensor.missing') }}" for field in NEW_FIELDS[kind]}
    options.update(
        {
            "template_type": kind,
            "additional_options": {"availability": "{{ has_value('sensor.ready') }}"},
            "advanced_options": {"availability": "{{ states('sensor.wrong') }}"},
            "turn_on": [
                {
                    "action": "test.action",
                    "data": {"value": "{{ states('sensor.action') }}"},
                }
            ],
            "set_temperature": "{{ states('sensor.action') }}",
            "unknown": "{{ states('sensor.unknown') }}",
        }
    )
    if kind == "water_heater":
        options["additional_options"]["away_mode"] = "{{ states('sensor.away') }}"
        options["away_mode"] = "{{ states('sensor.wrong_root') }}"
    values = dict(
        entry_id=kind, title=kind, version=2, minor_version=1, options=options
    )
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.mark.parametrize("kind", NEW_FIELDS)
def test_new_confirmed_fields(kind):
    e = entry(kind)
    before = repr(e.options)
    sources = _sources_from_entry(e)
    expected = [*NEW_FIELDS[kind], "additional_options.availability"]
    if kind == "water_heater":
        expected.append("additional_options.away_mode")
    assert [s.template_field for s in sources] == expected
    assert all(s.template_type == kind and s.source_id == kind for s in sources)
    assert repr(e.options) == before


@pytest.mark.parametrize("kind", NEW_FIELDS)
@pytest.mark.parametrize("version,minor", [(1, 3), (2, 2), (3, 0)])
def test_new_types_do_not_weaken_schema_boundary(kind, version, minor):
    with pytest.raises(ValueError, match="schema"):
        _sources_from_entry(entry(kind, version=version, minor_version=minor))


@pytest.mark.parametrize("kind", NEW_FIELDS)
@pytest.mark.parametrize("broken", ["root", "nested", "section"])
def test_malformed_new_source_isolated_from_valid_entry(kind, broken):
    bad = entry(kind)
    if broken == "root":
        bad.options[NEW_FIELDS[kind][0]] = []
    elif broken == "nested":
        field = "away_mode" if kind == "water_heater" else "availability"
        bad.options["additional_options"][field] = []
    else:
        bad.options["additional_options"] = []
    good = SimpleNamespace(
        entry_id="good",
        title="good",
        version=2,
        minor_version=1,
        options={"template_type": "sensor", "state": "{{ states('sensor.good') }}"},
    )
    hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_entries=lambda domain: [bad, good])
    )
    sources, errors = load_template_sources(hass)
    assert [s.source_id for s in sources] == ["good"]
    assert len(errors) == 1
    assert errors[0].source_id == kind
    assert "not a" in errors[0].error
