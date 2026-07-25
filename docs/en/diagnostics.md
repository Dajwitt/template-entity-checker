# Diagnostics

Download diagnostics under **Settings → Devices & services → Template Entity Checker**.

## Contents

| Field | Description |
|---|---|
| `integration_version` | integration version |
| `config_entry` | `entry_id`, `version`, `minor_version`, data, and options |
| `coordinator_available` | whether the coordinator is loaded |
| `last_update_success` | whether the last coordinator update succeeded |
| `last_exception` | last coordinator exception |
| `scan` | complete data from the latest scan |

The scan data includes active and ignored findings, parser diagnostics, source loading errors, and the status of the optional helper label:

- `missing_entities`
- `ignored_entities`
- `ignored_helper_label`
- `ignored_helper_sources`
- `ignored_matches`
- `parser_diagnostics`
- `load_errors`
- `template_types_scanned`
- `sources_scanned`
- `references_checked`
- `last_scan`
- `complete`
- `status`

## Redaction

Keys with these names are automatically redacted:

```json
["access_token", "password", "token"]
```

## Security

Review diagnostics before uploading them publicly. Access tokens, passwords, private Home Assistant URLs, and personal names do not belong in a GitHub issue.
