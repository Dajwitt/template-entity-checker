"""Sensor platform for Template Entity Checker."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME, VERSION
from .coordinator import TemplateEntityCheckerCoordinator

SENSOR_DESCRIPTION = SensorEntityDescription(
    key=DOMAIN,
    name=None,
    icon="mdi:code-braces-box",
    has_entity_name=True,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the result sensor."""
    coordinator: TemplateEntityCheckerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TemplateEntityCheckerSensor(coordinator, entry)])


class TemplateEntityCheckerSensor(CoordinatorEntity, SensorEntity):
    """Expose the latest scan count and full structured findings."""

    entity_description = SENSOR_DESCRIPTION

    def __init__(
        self, coordinator: TemplateEntityCheckerCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": NAME,
            "manufacturer": "Dajwitt",
            "model": NAME,
            "sw_version": VERSION,
        }

    @property
    def native_value(self) -> int:
        """Return missing, non-ignored unique entity count."""
        return len((self.coordinator.data or {}).get("missing_entities", {}))

    @property
    def extra_state_attributes(self) -> dict:
        """Return transparent scan details and separate error categories."""
        data = self.coordinator.data or {}
        failed = not self.coordinator.last_update_success
        return {
            "status": "update_failed" if failed else data.get("status", "waiting"),
            "complete": False if failed else data.get("complete", False),
            "scan_interval_minutes": self.coordinator.scan_interval_minutes,
            "template_types": data.get(
                "template_types", sorted(self.coordinator.template_types)
            ),
            "sources_scanned": data.get("sources_scanned", 0),
            "references_checked": data.get("references_checked", 0),
            "missing_entities": data.get("missing_entities", {}),
            "ignored_entities": data.get(
                "ignored_entities", self.coordinator.ignored_entities
            ),
            "ignored_matches": data.get("ignored_matches", {}),
            "parser_diagnostics": data.get("parser_diagnostics", []),
            "load_errors": data.get("load_errors", []),
            "last_scan": data.get("last_scan"),
            "last_error": str(self.coordinator.last_exception) if failed else None,
        }
