"""Config and options flow tests."""

from homeassistant import config_entries, data_entry_flow
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.template_entity_checker.const import (
    CONF_IGNORED_ENTITIES,
    CONF_NOTIFICATIONS,
    CONF_SCAN_INTERVAL,
    CONF_TEMPLATE_TYPES,
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
            CONF_TEMPLATE_TYPES: ["sensor", "binary_sensor"],
            CONF_IGNORED_ENTITIES: "sensor.ignored",
        },
    )
    assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_TEMPLATE_TYPES] == ["sensor", "binary_sensor"]


async def test_config_flow_rejects_dynamic_ignore_and_empty_types(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_SCAN_INTERVAL: 15,
            CONF_NOTIFICATIONS: True,
            CONF_TEMPLATE_TYPES: [],
            CONF_IGNORED_ENTITIES: "sensor.*",
        },
    )
    assert result["errors"] == {
        CONF_TEMPLATE_TYPES: "no_template_type_selected",
        CONF_IGNORED_ENTITIES: "invalid_entity_id",
    }


async def test_single_instance_abort(hass):
    MockConfigEntry(domain=DOMAIN, data={}).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_options_flow_updates_settings(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_SCAN_INTERVAL: 15,
            CONF_NOTIFICATIONS: True,
            CONF_TEMPLATE_TYPES: ["sensor"],
            CONF_IGNORED_ENTITIES: "",
        },
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_SCAN_INTERVAL: 30,
            CONF_NOTIFICATIONS: False,
            CONF_TEMPLATE_TYPES: ["binary_sensor"],
            CONF_IGNORED_ENTITIES: "sensor.ignored",
        },
    )
    assert result["type"] is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_SCAN_INTERVAL] == 30
