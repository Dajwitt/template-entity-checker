"""Diagnostics for Template Entity Checker."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, VERSION

TO_REDACT = {"access_token", "password", "token"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return redacted configuration and latest scan diagnostics."""
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    result: dict[str, Any] = {
        "integration_version": VERSION,
        "config_entry": {
            "entry_id": entry.entry_id,
            "version": entry.version,
            "minor_version": entry.minor_version,
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "coordinator_available": coordinator is not None,
        "last_update_success": (
            coordinator.last_update_success if coordinator is not None else None
        ),
        "last_exception": (
            str(coordinator.last_exception)
            if coordinator is not None and coordinator.last_exception
            else None
        ),
        "scan": coordinator.data if coordinator is not None else None,
    }
    return async_redact_data(result, TO_REDACT)
