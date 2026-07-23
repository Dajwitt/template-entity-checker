"""Template Entity Checker integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, Event, HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, PLATFORMS, SERVICE_SCAN_NOW
from .coordinator import TemplateEntityCheckerCoordinator

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration and its domain action once."""

    async def _async_scan_now(_call: ServiceCall) -> None:
        coordinators = list(hass.data.get(DOMAIN, {}).values())
        if not coordinators:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="not_loaded",
            )
        coordinator = coordinators[0]
        await coordinator.async_request_refresh()
        if not coordinator.last_update_success:
            raise HomeAssistantError(str(coordinator.last_exception))

    hass.services.async_register(DOMAIN, SERVICE_SCAN_NOW, _async_scan_now)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Template Entity Checker from a config entry."""
    coordinator = TemplateEntityCheckerCoordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if hass.state is CoreState.running:
        await coordinator.async_start_scanning()
    else:
        listener_consumed = False

        async def _async_start(_event: Event) -> None:
            nonlocal listener_consumed
            listener_consumed = True
            await coordinator.async_start_scanning()

        remove_listener = hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STARTED, _async_start
        )

        def _remove_pending_listener() -> None:
            nonlocal listener_consumed
            if listener_consumed:
                return
            listener_consumed = True
            remove_listener()

        entry.async_on_unload(_remove_pending_listener)

    entry.async_on_unload(entry.add_update_listener(_async_update_options))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload after an options change."""
    await hass.config_entries.async_reload(entry.entry_id)
