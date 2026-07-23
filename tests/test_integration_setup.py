"""Integration lifecycle and manual action tests."""

from unittest.mock import AsyncMock

import pytest
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.template_entity_checker import async_migrate_entry, async_setup
from custom_components.template_entity_checker.const import (
    CONF_NOTIFICATIONS,
    CONF_SCAN_INTERVAL,
    DOMAIN,
    SERVICE_SCAN_NOW,
)


async def test_scan_now_errors_when_entry_not_loaded(hass):
    assert await async_setup(hass, {})
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(DOMAIN, SERVICE_SCAN_NOW, {}, blocking=True)


async def test_scan_now_refreshes_loaded_coordinator(hass):
    assert await async_setup(hass, {})
    coordinator = AsyncMock()
    coordinator.last_update_success = True
    hass.data[DOMAIN] = {"entry-1": coordinator}
    await hass.services.async_call(DOMAIN, SERVICE_SCAN_NOW, {}, blocking=True)
    coordinator.async_request_refresh.assert_awaited_once()


async def test_real_config_entry_setup_creates_expected_sensor(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_SCAN_INTERVAL: 15,
            CONF_NOTIFICATIONS: False,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.template_entity_checker")
    assert state is not None
    assert state.state == "0"
    assert state.attributes["status"] == "ok"
    assert state.attributes["complete"] is True


async def test_migration_removes_legacy_template_type_selection(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        data={CONF_SCAN_INTERVAL: 15, "template_types": ["sensor"]},
        options={CONF_NOTIFICATIONS: True, "template_types": ["binary_sensor"]},
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry)
    assert entry.version == 2
    assert "template_types" not in entry.data
    assert "template_types" not in entry.options
