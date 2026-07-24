"""Tests for the isolated Template Helper ConfigEntry adapter."""

from types import SimpleNamespace

import pytest

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
        version=1,
        minor_version=2,
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
                "advanced_options": {
                    "availability": "{{ is_state('binary_sensor.ready', 'on') }}"
                },
                "unit_of_measurement": "%",
            }
        )


def test_sources_include_metadata_and_nested_field_path():
    sources = _sources_from_entry(FakeEntry())
    assert [(item.template_field, item.source_id) for item in sources] == [
        ("state", "entry-1"),
        ("advanced_options.availability", "entry-1"),
    ]
    assert all(item.helper == "Average humidity" for item in sources)
    assert all(item.source_type == "template_helper" for item in sources)


def test_every_template_helper_type_is_scanned():
    entry = FakeEntry(
        options={
            "name": "Simulated lock",
            "template_type": "lock",
            "state": "{{ is_state('binary_sensor.simulated_lock', 'on') }}",
        }
    )
    sources = _sources_from_entry(entry)
    assert [item.template_type for item in sources] == ["lock"]


def test_missing_template_type_becomes_load_error():
    entry = FakeEntry(options={"name": "Broken", "state": "{{ states('sensor.x') }}"})
    hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_entries=lambda domain: [entry])
    )
    sources, errors = load_template_sources(hass)
    assert sources == []
    assert errors[0].source_id == "entry-1"
    assert "template_type" in errors[0].error


def test_unknown_list_fields_are_not_scanned_as_templates():
    entry = FakeEntry(
        options={
            "name": "List helper",
            "template_type": "sensor",
            "attributes": ["{{ states('sensor.one') }}", "plain text"],
        }
    )
    sources = _sources_from_entry(entry)
    assert sources == []


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
    sources = _sources_from_entry(entry)
    assert [item.template_field for item in sources] == [
        "advanced_options.availability"
    ]


@pytest.mark.parametrize("version, minor_version", [(1, 3), (2, 1), (3, 0)])
def test_unknown_future_entry_schema_becomes_load_error(version, minor_version):
    entry = FakeEntry(version=version, minor_version=minor_version)
    hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_entries=lambda domain: [entry])
    )
    sources, errors = load_template_sources(hass)
    assert sources == []
    assert errors[0].error == (
        f"Unsupported Template Helper config entry schema {version}.{minor_version}"
    )


def test_device_tracker_has_value_templates_are_loaded_from_confirmed_fields():
    entry = FakeEntry(
        version=1,
        minor_version=2,
        options={
            "name": "Location helper",
            "template_type": "device_tracker",
            "in_zones": "{{ has_value('binary_sensor.location_source') }}",
            "advanced_options": {
                "availability": (
                    "{{ has_value('binary_sensor.availability_missing') }}"
                ),
                "location_accuracy": (
                    "{{ has_value('sensor.location_accuracy_source') }}"
                ),
            },
        },
    )

    sources = _sources_from_entry(entry)

    assert [item.template_field for item in sources] == [
        "in_zones",
        "advanced_options.availability",
        "advanced_options.location_accuracy",
    ]


@pytest.mark.parametrize(
    ("template_type", "root_fields"),
    [
        ("alarm_control_panel", ("value_template",)),
        ("binary_sensor", ("state",)),
        ("button", ()),
        ("cover", ("state", "position")),
        ("device_tracker", ("in_zones", "latitude", "longitude")),
        ("event", ("event_type", "event_types")),
        ("fan", ("state", "percentage")),
        ("image", ("url",)),
        ("light", ("state", "level", "hs", "temperature")),
        ("lock", ("state", "code_format")),
        ("number", ("state",)),
        ("select", ("state", "options")),
        ("sensor", ("state",)),
        ("switch", ("value_template",)),
        (
            "update",
            (
                "installed_version",
                "latest_version",
                "in_progress",
                "release_summary",
                "release_url",
                "title",
                "update_percentage",
            ),
        ),
        ("vacuum", ("state", "fan_speed")),
        (
            "weather",
            (
                "condition",
                "humidity",
                "temperature",
                "forecast_daily",
                "forecast_hourly",
            ),
        ),
    ],
)
def test_confirmed_template_fields_are_scanned_for_every_helper_type(
    template_type, root_fields
):
    section_name = "advanced_options"
    options = {
        "name": f"{template_type} helper",
        "template_type": template_type,
        section_name: {"availability": "{{ has_value('binary_sensor.available') }}"},
    }
    for index, field in enumerate(root_fields):
        options[field] = f"{{{{ states('sensor.source_{index}') }}}}"
    if template_type == "device_tracker":
        options[section_name]["location_accuracy"] = (
            "{{ states('sensor.location_accuracy') }}"
        )

    sources = _sources_from_entry(
        FakeEntry(
            version=1,
            minor_version=2,
            options=options,
        )
    )

    expected_paths = [*root_fields, f"{section_name}.availability"]
    if template_type == "device_tracker":
        expected_paths.append(f"{section_name}.location_accuracy")
    assert [item.template_field for item in sources] == expected_paths


def test_only_confirmed_nested_template_section_is_scanned():
    expected_section = "advanced_options"
    foreign_section = "additional_options"
    entry = FakeEntry(
        version=1,
        minor_version=2,
        options={
            "name": "Location helper",
            "template_type": "device_tracker",
            expected_section: {
                "availability": "{{ states('sensor.correct_availability') }}",
                "location_accuracy": "{{ states('sensor.correct_accuracy') }}",
            },
            foreign_section: {
                "availability": "{{ states('sensor.wrong_availability') }}",
                "location_accuracy": "{{ states('sensor.wrong_accuracy') }}",
            },
        },
    )

    sources = _sources_from_entry(entry)

    assert [item.template_field for item in sources] == [
        f"{expected_section}.availability",
        f"{expected_section}.location_accuracy",
    ]
    assert all("sensor.wrong" not in item.template for item in sources)


def test_action_and_metadata_strings_are_not_scanned_as_template_fields():
    entry = FakeEntry(
        options={
            "name": "Light helper",
            "template_type": "light",
            "state": "{{ states('light.source') }}",
            "turn_on": [
                {
                    "action": "light.turn_on",
                    "target": {"entity_id": "light.target"},
                    "data": {"message": "{{ states('sensor.action_value') }}"},
                }
            ],
            "unit_of_measurement": "{{ states('sensor.metadata') }}",
        }
    )

    sources = _sources_from_entry(entry)

    assert [item.template_field for item in sources] == ["state"]


def test_unknown_template_helper_type_becomes_load_error():
    entry = FakeEntry(
        options={
            "name": "Future helper",
            "template_type": "future_platform",
            "state": "{{ states('sensor.source') }}",
        }
    )
    hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_entries=lambda domain: [entry])
    )

    sources, errors = load_template_sources(hass)

    assert sources == []
    assert errors[0].error == "Unsupported Template Helper type future_platform"
