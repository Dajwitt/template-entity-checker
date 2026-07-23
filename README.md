# Template Entity Checker

[![Tests](https://github.com/Dajwitt/template-entity-checker/actions/workflows/tests.yml/badge.svg)](https://github.com/Dajwitt/template-entity-checker/actions/workflows/tests.yml)
[![Home Assistant validation](https://github.com/Dajwitt/template-entity-checker/actions/workflows/validate.yml/badge.svg)](https://github.com/Dajwitt/template-entity-checker/actions/workflows/validate.yml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://www.hacs.xyz/docs/faq/custom_repositories/)

Template Entity Checker is a read-only Home Assistant custom integration. It scans templates stored by UI-created Template Helpers and reports static entity references that no longer exist.

> **Scope: UI-created Template Helpers only.** Templates defined in `configuration.yaml`, `templates.yaml`, packages, or other included YAML files are not scanned.

**A focused complement, not a replacement:** Template Entity Checker does not replace Spook or Watchman. It focuses on UI-created Template Helpers and surfaces detailed findings directly in Home Assistant through its sensor and persistent notification as soon as a scan finds them—without opening and working through a separate text report.

It never renders or changes templates, never repairs references, never guesses dynamic entity IDs, and never reads or writes `.storage` directly.

## Version 0.1.0 scope

- UI-created Template Helpers represented by Home Assistant `template` Config Entries
- all UI-created Template Helper types are scanned automatically
- automatic scan after Home Assistant has fully started
- configurable interval from 1 to 1440 minutes
- manual `template_entity_checker.scan_now` action
- serialized scans through an async lock
- expected result entity `sensor.template_entity_checker`
- exact ignore list and transparent `ignored_matches`
- persistent notification updated only after a changed complete result
- notification dismissal after a clean complete scan
- `template_entity_checker_result_changed` event after the baseline changes
- diagnostics with separate missing references, parser diagnostics, and source load errors
- English and German UI text

## Supported static syntax

```jinja2
{{ states('sensor.example') }}
{{ state_attr('sensor.example', 'attribute') }}
{{ is_state('binary_sensor.example', 'on') }}
{{ is_state_attr('sensor.example', 'attribute', 'value') }}
{{ states.sensor.example.state }}
{{ states.binary_sensor.example }}
{{ expand('group.example') }}
```

Repeated occurrences are grouped without losing their count or line/column locations.

## Dynamic references

Dynamic IDs are not resolved:

```jinja2
{{ states('sensor.' ~ variable) }}
{{ state_attr(entity_variable, 'attribute') }}
```

They produce parser diagnostics and never a fabricated missing entity.

## What counts as missing?

An entity is missing only when it is absent from both:

1. the current Home Assistant state machine; and
2. the Home Assistant entity registry.

Therefore an entity is **not** missing when it is unavailable, unknown, disabled, or currently has no state but still has a registry entry.

## Installation through HACS

This pre-1.0 project is installed as a custom HACS repository:

1. Open HACS.
2. Add `https://github.com/Dajwitt/template-entity-checker` as a custom repository of type **Integration**.
3. Download Template Entity Checker.
4. Restart Home Assistant.
5. Open **Settings → Devices & services → Add integration** and select **Template Entity Checker**.

No `configuration.yaml` entry is required.

## Configuration

The Config Flow and Options Flow provide:

- scan interval;
- persistent notification toggle;
- exact ignored entity IDs, one per line.

Wildcards are intentionally not supported.

## Result sensor

The expected initial entity ID is `sensor.template_entity_checker`. Home Assistant's Entity Registry remains authoritative and users may rename it.

The state is the count of unique missing, non-ignored entities. Attributes include:

- `missing_entities`
- `ignored_entities`
- `ignored_matches`
- `parser_diagnostics`
- `load_errors`
- `template_types_scanned`
- `sources_scanned`
- `references_checked`
- `last_scan`
- `complete`
- `status`

Example structure:

```yaml
missing_entities:
  sensor.thermostat_flur_humidity:
    - helper: Average humidity
      source_type: template_helper
      source_id: example_internal_id
      template_field: state
      template_type: sensor
      reference: "states('sensor.thermostat_flur_humidity')"
      occurrence_count: 1
      locations:
        - line: 4
          column: 2
```

## Manual scan

```yaml
action: template_entity_checker.scan_now
```

If another scan is active, the trigger waits on the scan lock. Scans never run in parallel.

## Persistent notification

A single fixed notification is created for a changed complete result. Identical results do not create another notification. A clean complete scan dismisses the notification. A partial source-loading failure preserves the prior notification because incomplete input must not hide a real problem.

## Result-changed event

After the first complete scan establishes a baseline, a changed complete result fires:

```text
template_entity_checker_result_changed
```

Event data contains previous/current counts, added and removed IDs, full current findings, and scan time.

## Diagnostics

Download diagnostics from **Settings → Devices & services → Template Entity Checker**. Configuration, latest scan data, parser diagnostics, and load errors are included; common secret-shaped keys are redacted.

## Known limits

- The public Config Entry API is used read-only, but the `template` integration's option field structure is an internal schema and can change with Home Assistant releases. Access is isolated in `template_sources.py` and tested.
- YAML-based Template entities are not supported in 0.1.0 because Home Assistant provides no stable public API for another integration to enumerate all original YAML template sources.
- Templates in automations, scripts, scenes, dashboards, blueprints, and other integrations are not scanned.
- Jinja is not rendered or semantically executed. Conservative static extraction intentionally misses indirect references.
- Very large findings may approach Home Assistant's state-attribute size limits. Export and Repairs support are future work.

## Reproducible tests without hardware

See [`documentation/testbeispiele-ohne-hardware.md`](documentation/testbeispiele-ohne-hardware.md) for UI-created fixtures covering missing sensors, climate entities, locks, lights, binary sensors, switches, groups, duplicate occurrences, dynamic references, and a fully simulated controllable lock.

## Development

Requires Python 3.14.2 or newer and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --extra test
uv run ruff check custom_components tests scripts
uv run mypy custom_components/template_entity_checker
uv run pytest -q --cov=custom_components/template_entity_checker --cov-report=term-missing --cov-fail-under=90
uv run python scripts/check_legacy_references.py
```

## License

MIT. See [LICENSE](LICENSE).
