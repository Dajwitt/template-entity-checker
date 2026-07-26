# Template Entity Checker

[![Tests](https://github.com/Dajwitt/template-entity-checker/actions/workflows/tests.yml/badge.svg)](https://github.com/Dajwitt/template-entity-checker/actions/workflows/tests.yml)
[![Home Assistant validation](https://github.com/Dajwitt/template-entity-checker/actions/workflows/validate.yml/badge.svg)](https://github.com/Dajwitt/template-entity-checker/actions/workflows/validate.yml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://www.hacs.xyz/docs/faq/custom_repositories/)

Template Entity Checker is a read-only Home Assistant custom integration. It scans templates stored by UI-created Template Helpers and reports static entity references that no longer exist.

> **Scope: UI-created Template Helpers only.** Templates defined in `configuration.yaml`, `templates.yaml`, packages, or other included YAML files are not scanned.

**A focused complement, not a replacement:** Template Entity Checker does not replace Spook or Watchman. It focuses on UI-created Template Helpers and surfaces detailed findings directly in Home Assistant through its sensor and persistent notification as soon as a scan finds them—without opening and working through a separate text report.

It never renders or changes templates, never repairs references, never guesses dynamic entity IDs, and never reads or writes `.storage` directly.

## Documentation

- [Bilingual GitHub Pages documentation](https://dajwitt.github.io/template-entity-checker/)
- [English documentation](docs/en/index.md)
- [Deutsche Dokumentation](docs/de/index.md)

The same sources build the bilingual GitHub Pages site. The generated page is checked in CI so it cannot silently fall behind the Markdown documentation.

## Unreleased

- searchable Home Assistant label picker for the optional source-level exclusion; custom values are blocked, a previously saved deleted label remains removable, and at most one label can be saved

## Version 0.1.2

- UI-created Template Helpers represented by Home Assistant `template` Config Entries
- all 17 UI-created Template Helper types and their confirmed template fields are scanned automatically
- automatic scan after Home Assistant has fully started
- configurable interval from 1 to 1440 minutes
- manual `template_entity_checker.scan_now` action
- serialized scans through an async lock
- expected result entity `sensor.template_entity_checker`
- exact ignore list and transparent `ignored_matches`
- searchable multi-select for exact ignored entity IDs, including current findings
- optional source-level ignore through one freely selected Home Assistant label
- native Home Assistant toggle for persistent notifications
- `has_value` function, filter, and Jinja-test forms
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
{{ has_value('sensor.example') }}
{{ 'sensor.example' | has_value }}
{{ 'sensor.example' is has_value }}
{{ expand(['sensor.example_one', 'sensor.example_two']) }}
{{ expand('sensor.example_one', 'sensor.example_two') }}
```

Literal entity IDs inside `expand()` lists, tuples, and multiple arguments are checked individually. If an `expand()` collection mixes literal and dynamic values, the literal IDs are still checked while the dynamic part is reported separately and never guessed.

Repeated occurrences are grouped without losing their count or line/column locations. Function-like text inside normal text, Jinja comments, quoted strings, Jinja `is` / `is not` tests, macro and filter-block names, or calls on other objects is not treated as a Home Assistant entity reference. Local names follow Jinja scope and execution order: clear global calls before a same-scope binding remain detectable, locally resolved calls are ignored, and a child scope does not hide a later global call.

## Dynamic references

Dynamic IDs are not resolved:

```jinja2
{{ states('sensor.' ~ variable) }}
{{ state_attr(entity_variable, 'attribute') }}
{{ has_value(entity_variable) }}
{{ expand(['sensor.example', entity_variable]) }}
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
- searchable exact ignored entity IDs with free entry for missing IDs;
- one optional Home Assistant label for ignoring complete Template Helper sources.

Wildcards are intentionally not supported.

The label must be assigned directly to the entity created by the Template Helper.
Device and area labels are not inherited. Exact ignored entity IDs remain available
in parallel for individual missing targets. If the same missing entity is referenced
by both a labeled and an unlabeled helper, only the labeled helper's finding is
ignored.

## Result sensor

The expected initial entity ID is `sensor.template_entity_checker`. Home Assistant's Entity Registry remains authoritative and users may rename it.

The state is the count of unique missing, non-ignored entities. Attributes include:

- `missing_entities`
- `ignored_entities`
- `ignored_matches`
- `ignored_helper_label`
- `ignored_helper_sources`
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
  sensor.hallway_example_humidity:
    - helper: Average humidity
      source_type: template_helper
      source_id: example_internal_id
      template_field: state
      template_type: sensor
      reference: "states('sensor.hallway_example_humidity')"
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

After the first complete scan establishes a baseline, a change to the structured active `missing_entities` findings fires:

```text
template_entity_checker_result_changed
```

Event data contains previous/current counts, added and removed IDs, full current findings, and scan time.

## Diagnostics

Download diagnostics from **Settings → Devices & services → Template Entity Checker**. Configuration, latest scan data, parser diagnostics, and load errors are included; common secret-shaped keys are redacted.

## Known limits

- The public Config Entry API is used read-only, but the `template` integration's option field structure is an internal schema and can change with Home Assistant releases. Access is isolated in `template_sources.py` and tested. Unconfirmed newer schema versions are reported as source-load errors instead of being guessed.
- YAML-based Template entities are not supported because Home Assistant provides no stable public API for another integration to enumerate all original YAML template sources.
- Templates in automations, scripts, scenes, dashboards, blueprints, and other integrations are not scanned.
- Jinja is not rendered or semantically executed. Conservative static extraction intentionally misses indirect references.
- Very large findings may approach Home Assistant's state-attribute size limits. Export and Repairs support are future work.

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
