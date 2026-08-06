# How it works

## Scan process

```text
Home Assistant has fully started
        │
        ▼
Load UI-created Template Helpers through Config Entries
        │
        ▼
Extract confirmed template fields
        │
        ▼
Parse Jinja statically, never render it
        │
        ▼
Check references against the state machine and Entity Registry
        │
        ▼
Apply exact ignore IDs and the direct helper label per finding
        │
        ▼
Update the sensor
Update the notification after a changed complete result
Fire an event after a changed complete result
```

## Loading Template Helpers

The integration uses Home Assistant's public Config Entry API in read-only mode.

- no direct `.storage` access
- no template rendering or execution
- only confirmed `TemplateSelector` fields
- confirmed schema versions 1.0 through 1.2 and 2.0 through 2.1
- unknown or newer schemas are reported in `load_errors` instead of being guessed

## Supported Template Helper types

| Type | Scanned root fields |
|---|---|
| `alarm_control_panel` | `value_template` |
| `binary_sensor` | `state` |
| `button` | no root fields |
| `cover` | `state`, `position` |
| `device_tracker` | `in_zones`, `latitude`, `longitude` |
| `event` | `event_type`, `event_types` |
| `fan` | `state`, `percentage` |
| `image` | `url` |
| `light` | `state`, `level`, `hs`, `temperature` |
| `lock` | `state`, `code_format` |
| `number` | `state` |
| `select` | `state`, `options` |
| `sensor` | `state` |
| `switch` | `value_template` |
| `update` | `installed_version`, `latest_version`, `in_progress`, `release_summary`, `release_url`, `title`, `update_percentage` |
| `vacuum` | `state`, `fan_speed` |
| `weather` | `condition`, `humidity`, `temperature`, `forecast_daily`, `forecast_hourly` |

For schema 1.x, every type also checks `advanced_options.availability`; schema 2.x uses `additional_options.availability`. A `device_tracker` additionally checks `advanced_options.location_accuracy` or `additional_options.location_accuracy`, respectively. Missing fields are not counted as sources; present but empty fields are counted as scanned sources.

## When is an entity missing?

An entity is reported only when it exists in neither the state machine nor the Entity Registry. An entity that is `unavailable`, `unknown`, disabled, or currently without a state is not missing while a registry entry still exists.

## Exclusions

Exact ignore IDs suppress every finding for that target ID. The optional helper label is evaluated directly on the entities created by Template Helpers and suppresses only findings from those sources. Both exclusion paths move matching findings to `ignored_matches`.

## Automatic and manual scans

The first scan starts after Home Assistant has fully started. Later scans follow the configured interval. The `template_entity_checker.scan_now` action requests an immediate run. An async lock prevents parallel scans; a concurrent trigger waits.

## Partial failures

A source loading error produces `partial_error`. Successfully loaded sources remain visible in the sensor. An incomplete run changes neither the current notification nor the event result baseline.

## Grouping

Findings are grouped by entity ID. For each helper, field, and reference, the result retains the helper name, type, source ID, original reference, occurrence count, and every line and column location.
