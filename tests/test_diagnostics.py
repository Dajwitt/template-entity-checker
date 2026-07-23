"""Diagnostics tests."""

from types import SimpleNamespace

from custom_components.template_entity_checker.const import DOMAIN
from custom_components.template_entity_checker.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def test_diagnostics_include_separate_scan_categories(hass):
    coordinator = SimpleNamespace(
        last_update_success=True,
        last_exception=None,
        data={
            "missing_entities": {},
            "parser_diagnostics": [{"code": "dynamic_entity_reference"}],
            "load_errors": [],
        },
    )
    entry = SimpleNamespace(
        entry_id="entry-1",
        version=1,
        minor_version=1,
        data={"scan_interval": 15},
        options={},
    )
    hass.data[DOMAIN] = {entry.entry_id: coordinator}
    result = await async_get_config_entry_diagnostics(hass, entry)
    assert result["coordinator_available"] is True
    assert result["scan"]["parser_diagnostics"][0]["code"] == (
        "dynamic_entity_reference"
    )
