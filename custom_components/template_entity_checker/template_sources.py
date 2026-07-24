"""Read-only adapter for UI-created Home Assistant Template Helpers."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .models import SourceLoadError, TemplateSource

TEMPLATE_DOMAIN = "template"
SUPPORTED_ENTRY_VERSIONS = {1: 2, 2: 1}

# Confirmed TemplateSelector root fields from Home Assistant 2026.7.3.
TEMPLATE_FIELDS_BY_TYPE: dict[str, tuple[str, ...]] = {
    "alarm_control_panel": ("value_template",),
    "binary_sensor": ("state",),
    "button": (),
    "cover": ("state", "position"),
    "device_tracker": ("in_zones", "latitude", "longitude"),
    "event": ("event_type", "event_types"),
    "fan": ("state", "percentage"),
    "image": ("url",),
    "light": ("state", "level", "hs", "temperature"),
    "lock": ("state", "code_format"),
    "number": ("state",),
    "select": ("state", "options"),
    "sensor": ("state",),
    "switch": ("value_template",),
    "update": (
        "installed_version",
        "latest_version",
        "in_progress",
        "release_summary",
        "release_url",
        "title",
        "update_percentage",
    ),
    "vacuum": ("state", "fan_speed"),
    "weather": (
        "condition",
        "humidity",
        "temperature",
        "forecast_daily",
        "forecast_hourly",
    ),
}

_NESTED_OPTION_KEY_BY_VERSION = {1: "advanced_options", 2: "additional_options"}
_COMMON_NESTED_TEMPLATE_FIELDS = ("availability",)
_NESTED_TEMPLATE_FIELDS_BY_TYPE: dict[str, tuple[str, ...]] = {
    "device_tracker": ("location_accuracy",),
}


def load_template_sources(
    hass: HomeAssistant,
) -> tuple[list[TemplateSource], list[SourceLoadError]]:
    """Read template strings from Template Helper config entry options."""
    sources: list[TemplateSource] = []
    errors: list[SourceLoadError] = []

    for entry in hass.config_entries.async_entries(TEMPLATE_DOMAIN):
        try:
            sources.extend(_sources_from_entry(entry))
        except (KeyError, TypeError, ValueError) as err:
            errors.append(
                SourceLoadError(
                    source_id=entry.entry_id,
                    helper=entry.title,
                    error=str(err),
                )
            )
    return sources, errors


def _sources_from_entry(entry: ConfigEntry) -> list[TemplateSource]:
    """Convert confirmed template fields into independently scannable sources."""
    max_minor_version = SUPPORTED_ENTRY_VERSIONS.get(entry.version)
    if max_minor_version is None or entry.minor_version > max_minor_version:
        raise ValueError(
            "Unsupported Template Helper config entry schema "
            f"{entry.version}.{entry.minor_version}"
        )

    options = deepcopy(dict(entry.options))
    if not isinstance(options, Mapping):
        raise TypeError("Template Helper options are not a mapping")

    template_type = options.get("template_type")
    if not isinstance(template_type, str) or not template_type:
        raise KeyError("Template Helper has no template_type option")

    root_fields = TEMPLATE_FIELDS_BY_TYPE.get(template_type)
    if root_fields is None:
        raise ValueError(f"Unsupported Template Helper type {template_type}")

    helper = options.get("name") or entry.title
    if not isinstance(helper, str) or not helper:
        helper = entry.entry_id

    sources: list[TemplateSource] = []
    for field in root_fields:
        _append_template_source(
            sources,
            entry=entry,
            helper=helper,
            template_type=template_type,
            field=field,
            value=options.get(field),
        )

    nested_fields = _COMMON_NESTED_TEMPLATE_FIELDS + (
        _NESTED_TEMPLATE_FIELDS_BY_TYPE.get(template_type, ())
    )
    section_name = _NESTED_OPTION_KEY_BY_VERSION[entry.version]
    section = options.get(section_name)
    if section is not None:
        if not isinstance(section, Mapping):
            raise TypeError(f"Template Helper {section_name} is not a mapping")
        for field in nested_fields:
            _append_template_source(
                sources,
                entry=entry,
                helper=helper,
                template_type=template_type,
                field=f"{section_name}.{field}",
                value=section.get(field),
            )

    return sources


def _append_template_source(
    sources: list[TemplateSource],
    *,
    entry: ConfigEntry,
    helper: str,
    template_type: str,
    field: str,
    value: Any,
) -> None:
    """Append one confirmed TemplateSelector value when it is configured."""
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError(f"Template Helper field {field} is not a string")
    sources.append(
        TemplateSource(
            source_id=entry.entry_id,
            helper=helper,
            template_type=template_type,
            template_field=field,
            template=value,
        )
    )
