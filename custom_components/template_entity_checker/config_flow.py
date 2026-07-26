"""Config and options flows for Template Entity Checker."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback, valid_entity_id
from homeassistant.helpers import label_registry as lr
from homeassistant.helpers.selector import (
    BooleanSelector,
    BooleanSelectorConfig,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_IGNORED_ENTITIES,
    CONF_IGNORED_HELPER_LABEL,
    CONF_NOTIFICATIONS,
    CONF_SCAN_INTERVAL,
    DEFAULT_NOTIFICATIONS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    NAME,
)
from .coordinator import _configured_ignored_entities


class TemplateEntityCheckerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle initial setup."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure the single integration instance."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors = _validate_input(user_input) if user_input is not None else {}
        if user_input is not None and not errors:
            return self.async_create_entry(
                title=NAME, data=_normalized_input(user_input)
            )

        values = user_input or {}
        return self.async_show_form(
            step_id="user",
            data_schema=_settings_schema(
                values,
                label_options=_label_options(self.hass, values),
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow."""
        return TemplateEntityCheckerOptionsFlow()


class TemplateEntityCheckerOptionsFlow(OptionsFlow):
    """Handle runtime options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Update settings."""
        current = {**self.config_entry.data, **self.config_entry.options}
        errors = _validate_input(user_input) if user_input is not None else {}
        if user_input is not None and not errors:
            saved = _normalized_input(user_input)
            saved.setdefault(CONF_IGNORED_ENTITIES, [])
            return self.async_create_entry(data=saved)
        values = user_input or current
        return self.async_show_form(
            step_id="init",
            data_schema=_settings_schema(
                values,
                ignored_options=_ignored_entity_options(
                    self.hass,
                    self.config_entry.entry_id,
                    values,
                ),
                label_options=_label_options(self.hass, values),
            ),
            errors=errors,
        )


def _settings_schema(
    values: dict[str, Any],
    *,
    ignored_options: list[str] | None = None,
    label_options: list[SelectOptionDict] | None = None,
) -> vol.Schema:
    """Build the shared config/options schema."""
    ignored = _configured_ignored_entities(values)
    options = sorted(set(ignored_options or ()) | set(ignored))
    ignored_labels = _configured_ignored_helper_labels(values)
    label_marker = vol.Optional(CONF_IGNORED_HELPER_LABEL)
    if ignored_labels:
        label_marker = vol.Optional(
            CONF_IGNORED_HELPER_LABEL,
            description={"suggested_value": ignored_labels},
        )
    return vol.Schema(
        {
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=values.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440)),
            vol.Required(
                CONF_NOTIFICATIONS,
                default=values.get(CONF_NOTIFICATIONS, DEFAULT_NOTIFICATIONS),
            ): BooleanSelector(BooleanSelectorConfig()),
            vol.Optional(
                CONF_IGNORED_ENTITIES,
                description={"suggested_value": ignored},
            ): SelectSelector(
                SelectSelectorConfig(
                    options=options,
                    multiple=True,
                    custom_value=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            label_marker: SelectSelector(
                SelectSelectorConfig(
                    options=label_options or [],
                    multiple=True,
                    custom_value=False,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )


def _ignored_entity_options(
    hass: Any, entry_id: str, values: dict[str, Any]
) -> list[str]:
    """Return current, previous, and configured missing IDs for the dropdown."""
    options = set(_configured_ignored_entities(values))
    coordinator = hass.data.get(DOMAIN, {}).get(entry_id)
    scan = getattr(coordinator, "data", None) or {}
    for key in ("missing_entities", "ignored_matches"):
        findings = scan.get(key, {})
        if isinstance(findings, dict):
            options.update(item for item in findings if isinstance(item, str))
    return sorted(options)


def _label_options(
    hass: HomeAssistant, values: dict[str, Any]
) -> list[SelectOptionDict]:
    """Return current labels with stable IDs and current display names."""
    options = [
        SelectOptionDict(value=label.label_id, label=label.name)
        for label in lr.async_get(hass).async_list_labels()
    ]
    for configured in _configured_ignored_helper_labels(values):
        if all(option["value"] != configured for option in options):
            options.append(SelectOptionDict(value=configured, label=configured))
    return sorted(
        options, key=lambda option: (option["label"].casefold(), option["value"])
    )


def _validate_input(user_input: dict[str, Any] | None) -> dict[str, str]:
    """Validate exact ignored entity IDs."""
    if user_input is None:
        return {}
    errors: dict[str, str] = {}
    if any(
        not valid_entity_id(entity_id)
        for entity_id in _configured_ignored_entities(user_input)
    ):
        errors[CONF_IGNORED_ENTITIES] = "invalid_entity_id"
    if len(_configured_ignored_helper_labels(user_input)) > 1:
        errors[CONF_IGNORED_HELPER_LABEL] = "single_label_only"
    return errors


def _configured_ignored_helper_labels(values: dict[str, Any]) -> list[str]:
    """Return the UI label selection as a list for the searchable picker."""
    configured = values.get(CONF_IGNORED_HELPER_LABEL)
    if isinstance(configured, str):
        return [configured] if configured else []
    if isinstance(configured, (list, tuple)):
        return [item for item in configured if isinstance(item, str) and item]
    return []


def _normalized_input(user_input: dict[str, Any]) -> dict[str, Any]:
    """Keep the persisted label setting backward-compatible as one string."""
    saved = dict(user_input)
    labels = _configured_ignored_helper_labels(user_input)
    saved[CONF_IGNORED_HELPER_LABEL] = labels[0] if labels else ""
    return saved
