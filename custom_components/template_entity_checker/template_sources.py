"""Read-only adapter for UI-created Home Assistant Template Helpers."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .models import SourceLoadError, TemplateSource

TEMPLATE_DOMAIN = "template"


def load_template_sources(
    hass: HomeAssistant, selected_types: set[str]
) -> tuple[list[TemplateSource], list[SourceLoadError]]:
    """Read template strings from Template Helper config entry options.

    ConfigEntry access is public. The foreign integration's options schema is not a
    public contract, so all schema knowledge is kept inside this adapter.
    """
    sources: list[TemplateSource] = []
    errors: list[SourceLoadError] = []

    for entry in hass.config_entries.async_entries(TEMPLATE_DOMAIN):
        try:
            sources.extend(_sources_from_entry(entry, selected_types))
        except (KeyError, TypeError, ValueError) as err:
            errors.append(
                SourceLoadError(
                    source_id=entry.entry_id,
                    helper=entry.title,
                    error=str(err),
                )
            )
    return sources, errors


def _sources_from_entry(
    entry: ConfigEntry, selected_types: set[str]
) -> list[TemplateSource]:
    """Convert one Template Helper entry into independently scannable strings."""
    options = entry.options
    if not isinstance(options, Mapping):
        raise TypeError("Template Helper options are not a mapping")

    template_type = options.get("template_type")
    if not isinstance(template_type, str) or not template_type:
        raise KeyError("Template Helper has no template_type option")
    if template_type not in selected_types:
        return []

    helper = options.get("name") or entry.title
    if not isinstance(helper, str) or not helper:
        helper = entry.entry_id

    sources: list[TemplateSource] = []
    for field, value in options.items():
        if field in {"name", "template_type"}:
            continue
        for path, template in _walk_strings(value, str(field)):
            if not _may_contain_template_reference(template):
                continue
            sources.append(
                TemplateSource(
                    source_id=entry.entry_id,
                    helper=helper,
                    template_type=template_type,
                    template_field=path,
                    template=template,
                )
            )
    return sources


def _walk_strings(value: Any, path: str) -> Iterator[tuple[str, str]]:
    """Yield string values with deterministic field paths."""
    if isinstance(value, str):
        yield path, value
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk_strings(child, f"{path}.{key}")
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            yield from _walk_strings(child, f"{path}[{index}]")


def _may_contain_template_reference(value: str) -> bool:
    """Avoid treating arbitrary helper metadata as a template source."""
    markers = ("states", "state_attr", "is_state", "is_state_attr", "expand")
    return any(marker in value for marker in markers)
