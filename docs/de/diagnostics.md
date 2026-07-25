# Diagnostik

Diagnostik kann unter **Einstellungen → Geräte & Dienste → Template Entity Checker** heruntergeladen werden.

## Inhalt

| Feld | Beschreibung |
|---|---|
| `integration_version` | Version der Integration |
| `config_entry` | `entry_id`, `version`, `minor_version`, Daten und Optionen |
| `coordinator_available` | ob der Coordinator geladen ist |
| `last_update_success` | ob der letzte Coordinator-Lauf erfolgreich war |
| `last_exception` | letzte Coordinator-Exception |
| `scan` | vollständige Daten des letzten Scans |

Die Scan-Daten enthalten unter anderem aktive und ignorierte Funde, Parser-Diagnosen, Quell-Ladefehler sowie den Status des optionalen Helfer-Labels:

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

## Redaktion

Schlüssel mit diesen Namen werden automatisch geschwärzt:

```json
["access_token", "password", "token"]
```

## Sicherheit

Prüfe Diagnosedaten trotzdem vor einem öffentlichen Upload. Access-Tokens, Passwörter, private Home-Assistant-URLs und persönliche Namen gehören nicht in ein GitHub-Issue.
