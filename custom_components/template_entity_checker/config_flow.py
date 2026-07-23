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
from homeassistant.core import callback, valid_entity_id
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
)

from .const import (
    CONF_IGNORED_ENTITIES,
    CONF_NOTIFICATIONS,
    CONF_SCAN_INTERVAL,
    DEFAULT_IGNORED_ENTITIES,
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
            return self.async_create_entry(title=NAME, data=user_input)

        values = user_input or {}
        return self.async_show_form(
            step_id="user",
            data_schema=_settings_schema(values),
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
            return self.async_create_entry(data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=_settings_schema(user_input or current),
            errors=errors,
        )


def _settings_schema(values: dict[str, Any]) -> vol.Schema:
    """Build the shared config/options schema."""
    ignored = values.get(CONF_IGNORED_ENTITIES, DEFAULT_IGNORED_ENTITIES)
    if isinstance(ignored, (list, tuple)):
        ignored = "\n".join(ignored)
    return vol.Schema(
        {
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=values.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440)),
            vol.Required(
                CONF_NOTIFICATIONS,
                default=values.get(CONF_NOTIFICATIONS, DEFAULT_NOTIFICATIONS),
            ): bool,
            vol.Optional(
                CONF_IGNORED_ENTITIES,
                default=DEFAULT_IGNORED_ENTITIES,
                description={"suggested_value": ignored},
            ): TextSelector(TextSelectorConfig(multiline=True)),
        }
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
    return errors
