"""Tests for the isolated Template Helper ConfigEntry adapter."""

from types import SimpleNamespace

from custom_components.template_entity_checker.template_sources import (
    _sources_from_entry,
    load_template_sources,
)


class FakeEntry:
    def __init__(
        self,
        entry_id="entry-1",
        title="Humidity",
        options=None,
        version=2,
        minor_version=1,
    ):
        self.entry_id = entry_id
        self.title = title
        self.version = version
        self.minor_version = minor_version
        self.options = (
            options
            if options is not None
            else {
                "name": "Average humidity",
                "template_type": "sensor",
                "state": "{{ states('sensor.humidity') }}",
                "additional_options": {
                    "availability": "{{ is_state('binary_sensor.ready', 'on') }}"
                },
                "unit_of_measurement": "%",
            }
        )


def test_sources_include_metadata_and_nested_field_path():
    sources = _sources_from_entry(FakeEntry(), {"sensor"})
    assert [(item.template_field, item.source_id) for item in sources] == [
        ("state", "entry-1"),
        ("additional_options.availability", "entry-1"),
    ]
    assert all(item.helper == "Average humidity" for item in sources)
    assert all(item.source_type == "template_helper" for item in sources)


def test_unselected_type_is_skipped():
    assert _sources_from_entry(FakeEntry(), {"binary_sensor"}) == []


def test_missing_template_type_becomes_load_error():
    entry = FakeEntry(options={"name": "Broken", "state": "{{ states('sensor.x') }}"})
    hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_entries=lambda domain: [entry])
    )
    sources, errors = load_template_sources(hass, {"sensor"})
    assert sources == []
    assert errors[0].source_id == "entry-1"
    assert "template_type" in errors[0].error


def test_list_fields_have_stable_paths():
    entry = FakeEntry(
        options={
            "name": "List helper",
            "template_type": "sensor",
            "attributes": ["{{ states('sensor.one') }}", "plain text"],
        }
    )
    sources = _sources_from_entry(entry, {"sensor"})
    assert [item.template_field for item in sources] == ["attributes[0]"]


def test_stable_2026_7_advanced_options_schema_is_supported():
    entry = FakeEntry(
        version=1,
        minor_version=2,
        options={
            "name": "Stable helper",
            "template_type": "sensor",
            "advanced_options": {"availability": "{{ states('sensor.stable') }}"},
        },
    )
    sources = _sources_from_entry(entry, {"sensor"})
    assert [item.template_field for item in sources] == [
        "advanced_options.availability"
    ]


def test_unknown_future_entry_schema_becomes_load_error():
    entry = FakeEntry(version=3, minor_version=0)
    hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_entries=lambda domain: [entry])
    )
    sources, errors = load_template_sources(hass, {"sensor"})
    assert sources == []
    assert errors[0].error == "Unsupported Template Helper config entry schema 3.0"
