# Result sensor

The integration normally creates `sensor.template_entity_checker`. Home Assistant's Entity Registry remains authoritative, so users can rename the entity.

## State

| State | Meaning |
|---|---|
| `0` | no active missing entities |
| `N` | N unique missing, non-ignored entity IDs |

## Attributes

| Attribute | Type | Description |
|---|---|---|
| `status` | string | `ok`, `missing_entities`, `partial_error`, `update_failed`, or `waiting` |
| `complete` | bool | `true` when every source loaded successfully |
| `scan_interval_minutes` | int | configured scan interval |
| `template_types_scanned` | list | Template Helper types actually scanned |
| `sources_scanned` | int | number of template fields scanned |
| `references_checked` | int | number of statically extracted reference occurrences |
| `missing_entities` | dict | active findings grouped by entity ID |
| `ignored_entities` | list | configured exact ignore IDs |
| `ignored_helper_label` | dict/null | label ID, current name, and availability |
| `ignored_helper_sources` | list | helpers actually excluded through the label |
| `ignored_matches` | dict | findings suppressed through either exclusion type |
| `parser_diagnostics` | list | dynamic, invalid, or syntactically broken references |
| `load_errors` | list | source loading errors |
| `last_scan` | string/null | ISO timestamp of the last scan |
| `last_error` | string/null | last coordinator exception |

## Recorder history

The large detail attributes `missing_entities`, `ignored_entities`, `ignored_helper_sources`, `ignored_matches`, `parser_diagnostics`, and `load_errors` remain visible on the current sensor state but are not stored in Recorder history. This prevents oversized attribute rows. Compact values such as status, completeness, counts, and scan time remain available historically.

## Example active finding

```yaml
sensor.garden_room_example_old_value:
  - helper: Garden room average
    source_type: template_helper
    source_id: example_internal_id
    template_field: state
    template_type: sensor
    reference: "states('sensor.garden_room_example_old_value')"
    occurrence_count: 1
    locations:
      - line: 4
        column: 2
```

## Example selected helper label

```yaml
ignored_helper_label:
  label_id: example_ignore_check
  name: Ignore check
  available: true
ignored_helper_sources:
  - source_id: example_helper_entry_id
    helper: Garden room comparison
```

If the stored label is later deleted, its ID remains transparent, `name` becomes `null`, `available` becomes `false`, and no sources are excluded through it.

## Status values

| Status | Meaning |
|---|---|
| `ok` | complete scan without active findings |
| `missing_entities` | complete scan with active findings |
| `partial_error` | at least one source could not be loaded |
| `update_failed` | the entire coordinator update failed |
| `waiting` | integration loaded; the first scan has not run yet |
