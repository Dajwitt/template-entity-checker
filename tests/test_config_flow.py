"""Config and options flow tests."""

from homeassistant import config_entries, data_entry_flow
from homeassistant.helpers.selector import (
    BooleanSelector,
    LabelSelector,
    SelectSelector,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.template_entity_checker.const import (
    CONF_IGNORED_ENTITIES,
    CONF_NOTIFICATIONS,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)


async def test_config_flow_creates_entry(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is data_entry_flow.FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_SCAN_INTERVAL: 15,
            CONF_NOTIFICATIONS: True,
            CONF_IGNORED_ENTITIES: ["sensor.ignored"],
            "ignored_helper_label": "maintenance_ignore",
        },
    )
    assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert "template_types" not in result["data"]


async def test_config_flow_rejects_dynamic_ignore(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_SCAN_INTERVAL: 15,
            CONF_NOTIFICATIONS: True,
            CONF_IGNORED_ENTITIES: ["sensor.*"],
        },
    )
    assert result["errors"] == {CONF_IGNORED_ENTITIES: "invalid_entity_id"}


async def test_single_instance_abort(hass):
    MockConfigEntry(domain=DOMAIN, data={}).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


def _schema_field(result, key):
    for marker, validator in result["data_schema"].schema.items():
        if marker.schema == key:
            return marker, validator
    raise AssertionError(f"Missing schema field: {key}")


async def test_config_flow_uses_modern_selectors(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    _, notifications = _schema_field(result, CONF_NOTIFICATIONS)
    _, ignored_entities = _schema_field(result, CONF_IGNORED_ENTITIES)
    _, ignored_label = _schema_field(result, "ignored_helper_label")

    assert isinstance(notifications, BooleanSelector)
    assert isinstance(ignored_entities, SelectSelector)
    assert ignored_entities.config["multiple"] is True
    assert ignored_entities.config["custom_value"] is True
    assert ignored_entities.config["mode"] == "dropdown"
    assert isinstance(ignored_label, LabelSelector)
    assert ignored_label.config["multiple"] is False


async def test_options_flow_updates_settings(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_SCAN_INTERVAL: 15,
            CONF_NOTIFICATIONS: True,
            "template_types": ["sensor"],
            CONF_IGNORED_ENTITIES: "",
        },
    )
    entry.add_to_hass(hass)
    hass.data[DOMAIN] = {
        entry.entry_id: type(
            "Coordinator",
            (),
            {
                "data": {
                    "missing_entities": {"sensor.current_missing": []},
                    "ignored_matches": {"sensor.previously_ignored": []},
                }
            },
        )()
    }
    result = await hass.config_entries.options.async_init(entry.entry_id)
    _, ignored_entities = _schema_field(result, CONF_IGNORED_ENTITIES)
    assert set(ignored_entities.config["options"]) == {
        "sensor.current_missing",
        "sensor.previously_ignored",
    }
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_SCAN_INTERVAL: 30,
            CONF_NOTIFICATIONS: False,
            CONF_IGNORED_ENTITIES: ["sensor.ignored"],
            "ignored_helper_label": "maintenance_ignore",
        },
    )
    assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_SCAN_INTERVAL] == 30
    assert result["data"][CONF_IGNORED_ENTITIES] == ["sensor.ignored"]
    assert result["data"]["ignored_helper_label"] == "maintenance_ignore"
    assert "template_types" not in result["data"]


async def test_options_flow_can_clear_ignores_from_initial_data(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_SCAN_INTERVAL: 15,
            CONF_NOTIFICATIONS: True,
            CONF_IGNORED_ENTITIES: "sensor.old_ignore",
            "ignored_helper_label": "old_label",
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_SCAN_INTERVAL: 15,
            CONF_NOTIFICATIONS: True,
        },
    )

    assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_IGNORED_ENTITIES] == []
    assert result["data"]["ignored_helper_label"] == ""
