"""Persistent notification rendering for Template Entity Checker."""

from __future__ import annotations

from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant

from .const import NAME, NOTIFICATION_ID


def update_notification(
    hass: HomeAssistant,
    missing_entities: dict[str, list[dict[str, Any]]],
    *,
    enabled: bool,
) -> None:
    """Create/update the fixed notification, or dismiss it when clean/disabled."""
    if not enabled or not missing_entities:
        persistent_notification.async_dismiss(hass, NOTIFICATION_ID)
        return

    language = getattr(hass.config, "language", "en")
    persistent_notification.async_create(
        hass,
        notification_message(missing_entities, language),
        title=notification_title(len(missing_entities), language),
        notification_id=NOTIFICATION_ID,
    )


def notification_title(count: int, language: str) -> str:
    """Return a localized notification title."""
    if language.lower().startswith("de"):
        noun = "fehlende Entity" if count == 1 else "fehlende Entities"
    else:
        noun = "missing entity" if count == 1 else "missing entities"
    return f"{NAME}: {count} {noun}"


def notification_message(
    missing_entities: dict[str, list[dict[str, Any]]], language: str
) -> str:
    """Render a compact helper-grouped Markdown message."""
    german = language.lower().startswith("de")
    grouped: dict[str, list[str]] = {}
    for entity_id, findings in missing_entities.items():
        helpers = {str(item.get("helper", "Unknown helper")) for item in findings}
        for helper in helpers:
            grouped.setdefault(helper, []).append(entity_id)

    blocks = ["**Template-Helfer**" if german else "**Template Helpers**"]
    for helper in sorted(grouped):
        lines = [helper]
        lines.extend(f"• `{entity_id}`" for entity_id in sorted(grouped[helper]))
        blocks.append("\n".join(lines))
    footer = (
        "Vollständige Liste: Sensorattribut `missing_entities`"
        if german
        else "Complete list: sensor attribute `missing_entities`"
    )
    blocks.append(footer)
    return "\n\n".join(blocks)
