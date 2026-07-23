"""Coordinator for periodic Template Helper scans."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from collections import defaultdict
from dataclasses import asdict
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_IGNORED_ENTITIES,
    CONF_NOTIFICATIONS,
    CONF_SCAN_INTERVAL,
    DEFAULT_IGNORED_ENTITIES,
    DEFAULT_NOTIFICATIONS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    EVENT_RESULT_CHANGED,
)
from .models import StaticReference, TemplateSource
from .notifications import update_notification
from .parser import parse_template
from .template_sources import load_template_sources

_LOGGER = logging.getLogger(__name__)


class TemplateEntityCheckerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Scan Template Helper config entries without rendering or changing them."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator from merged config-entry settings."""
        settings = {**entry.data, **entry.options}
        interval = int(settings.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        self.scan_interval_minutes = interval
        self.notifications_enabled = bool(
            settings.get(CONF_NOTIFICATIONS, DEFAULT_NOTIFICATIONS)
        )
        self.ignored_entities = _configured_ignored_entities(settings)
        self._configured_interval = timedelta(minutes=interval)
        self._scan_lock = asyncio.Lock()
        self._scanning_started = False
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=None,
        )

    async def async_start_scanning(self) -> None:
        """Run the first scan only after HA startup and then enable polling."""
        if self._scanning_started:
            return
        self._scanning_started = True
        self.update_interval = self._configured_interval  # type: ignore[misc]
        await self.async_refresh()

    async def _async_update_data(self) -> dict[str, Any]:
        """Serialize automatic and manual scans; a concurrent trigger waits."""
        async with self._scan_lock:
            return await self._async_scan()

    async def _async_scan(self) -> dict[str, Any]:
        """Load all UI-created Template Helpers and aggregate safe static results."""
        sources, source_errors = load_template_sources(self.hass)
        references: list[tuple[TemplateSource, StaticReference]] = []
        parser_diagnostics: list[dict[str, Any]] = []
        load_errors = [error.as_dict() for error in source_errors]

        for source in sources:
            try:
                parsed, diagnostics = parse_template(source.template)
            except (  # pragma: no cover - defensive
                TypeError,
                ValueError,
                re.error,
            ) as err:
                load_errors.append(
                    {
                        "source_id": source.source_id,
                        "helper": source.helper,
                        "template_field": source.template_field,
                        "error": str(err),
                    }
                )
                continue
            references.extend((source, reference) for reference in parsed)
            parser_diagnostics.extend(
                {
                    **asdict(diagnostic),
                    "source_type": source.source_type,
                    "source_id": source.source_id,
                    "helper": source.helper,
                    "template_type": source.template_type,
                    "template_field": source.template_field,
                }
                for diagnostic in diagnostics
            )

        registry = er.async_get(self.hass)
        detected = _missing_entity_findings(references, self.hass.states, registry)
        missing_entities, ignored_matches = _partition_ignored(
            detected, set(self.ignored_entities)
        )
        scan_time = dt_util.now().isoformat()
        complete = not load_errors
        current_signature = _result_signature(missing_entities)
        previous_signature = (self.data or {}).get("result_signature")

        if not self.notifications_enabled:
            update_notification(self.hass, {}, enabled=False)
        elif complete and current_signature != previous_signature:
            update_notification(
                self.hass, missing_entities, enabled=self.notifications_enabled
            )

        if complete:
            _fire_result_changed_event(
                self.hass,
                self.data,
                missing_entities,
                current_signature,
                scan_time,
            )

        return {
            "status": (
                "partial_error"
                if load_errors
                else "missing_entities"
                if missing_entities
                else "ok"
            ),
            "complete": complete,
            "last_scan": scan_time,
            "sources_scanned": len(sources),
            "references_checked": len(references),
            "missing_entities": missing_entities,
            "ignored_entities": self.ignored_entities,
            "ignored_matches": ignored_matches,
            "parser_diagnostics": parser_diagnostics,
            "load_errors": load_errors,
            "result_signature": current_signature,
            "template_types_scanned": sorted(
                {source.template_type for source in sources}
            ),
        }


def _configured_ignored_entities(settings: dict[str, Any]) -> list[str]:
    """Normalize exact entity IDs from text or a sequence."""
    raw = settings.get(CONF_IGNORED_ENTITIES, DEFAULT_IGNORED_ENTITIES)
    values = raw.replace(",", "\n").splitlines() if isinstance(raw, str) else raw
    if not isinstance(values, (list, tuple)):
        return []
    return list(
        dict.fromkeys(
            item.strip() for item in values if isinstance(item, str) and item.strip()
        )
    )


def _missing_entity_findings(
    references: list[tuple[TemplateSource, StaticReference]],
    states: Any,
    registry: Any,
) -> dict[str, list[dict[str, Any]]]:
    """Return grouped findings absent from both state machine and registry."""
    grouped: dict[tuple[str, str, str, str, str, str], dict[str, Any]] = {}
    for source, reference in references:
        if states.get(reference.entity_id) is not None:
            continue
        if registry.async_get(reference.entity_id) is not None:
            continue
        key = (
            reference.entity_id,
            source.source_id,
            source.template_field,
            source.template_type,
            source.helper,
            reference.reference,
        )
        finding = grouped.setdefault(
            key,
            {
                "helper": source.helper,
                "source_type": source.source_type,
                "source_id": source.source_id,
                "template_field": source.template_field,
                "template_type": source.template_type,
                "reference": reference.reference,
                "occurrence_count": 0,
                "locations": [],
            },
        )
        finding["occurrence_count"] += 1
        finding["locations"].append(
            {"line": reference.line, "column": reference.column}
        )

    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for key, finding in grouped.items():
        result[key[0]].append(finding)
    return {
        entity_id: sorted(
            findings,
            key=lambda item: (
                item["helper"],
                item["template_field"],
                item["reference"],
            ),
        )
        for entity_id, findings in sorted(result.items())
    }


def _partition_ignored(
    detected: dict[str, list[dict[str, Any]]], ignored: set[str]
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    """Separate exact ignored IDs without hiding their findings."""
    active = {key: value for key, value in detected.items() if key not in ignored}
    ignored_matches = {key: value for key, value in detected.items() if key in ignored}
    return active, ignored_matches


def _result_signature(missing_entities: dict[str, Any]) -> str:
    """Return a deterministic complete-result fingerprint."""
    return json.dumps(missing_entities, sort_keys=True, separators=(",", ":"))


def _fire_result_changed_event(
    hass: HomeAssistant,
    previous_data: dict[str, Any] | None,
    missing_entities: dict[str, Any],
    current_signature: str,
    scan_time: str,
) -> None:
    """Fire after baseline only when a complete structured result changes."""
    if previous_data is None or not previous_data.get("complete", False):
        return
    if previous_data.get("result_signature") == current_signature:
        return
    previous = previous_data.get("missing_entities", {})
    previous_ids = set(previous)
    current_ids = set(missing_entities)
    hass.bus.async_fire(
        EVENT_RESULT_CHANGED,
        {
            "previous_count": len(previous),
            "current_count": len(missing_entities),
            "added_entities": sorted(current_ids - previous_ids),
            "removed_entities": sorted(previous_ids - current_ids),
            "missing_entities": missing_entities,
            "scan_time": scan_time,
        },
    )
