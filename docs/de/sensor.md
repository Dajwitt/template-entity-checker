# Result-Sensor

Die Integration erstellt standardmäßig `sensor.template_entity_checker`. Home Assistants Entity Registry bleibt führend; der Sensor kann umbenannt werden.

## Zustand

| Zustand | Bedeutung |
|---|---|
| `0` | keine aktiven fehlenden Entities |
| `N` | N eindeutige fehlende, nicht ignorierte Entity-IDs |

## Attribute

| Attribut | Typ | Beschreibung |
|---|---|---|
| `status` | string | `ok`, `missing_entities`, `partial_error`, `update_failed` oder `waiting` |
| `complete` | bool | `true`, wenn alle Quellen fehlerfrei geladen wurden |
| `scan_interval_minutes` | int | konfiguriertes Scan-Intervall |
| `template_types_scanned` | list | tatsächlich gescannte Template-Typen |
| `sources_scanned` | int | Anzahl gescannter Template-Felder |
| `references_checked` | int | Anzahl statisch extrahierter Referenzvorkommen |
| `missing_entities` | dict | aktive Funde, gruppiert nach Entity-ID |
| `ignored_entities` | list | konfigurierte exakte Ignore-IDs |
| `ignored_helper_label` | dict/null | Label-ID, aktueller Name und Verfügbarkeit |
| `ignored_helper_sources` | list | tatsächlich über das Label ausgeschlossene Helfer |
| `ignored_matches` | dict | durch beide Ausschlussarten unterdrückte Funde |
| `parser_diagnostics` | list | dynamische, ungültige oder syntaktisch fehlerhafte Referenzen |
| `load_errors` | list | Quell-Ladefehler |
| `last_scan` | string/null | ISO-Zeitstempel des letzten Scans |
| `last_error` | string/null | letzte Coordinator-Exception |

## Beispiel: aktiver Fund

```yaml
sensor.gartenhaus_beispiel_altwert:
  - helper: Durchschnitt Gartenhaus
    source_type: template_helper
    source_id: example_internal_id
    template_field: state
    template_type: sensor
    reference: "states('sensor.gartenhaus_beispiel_altwert')"
    occurrence_count: 1
    locations:
      - line: 4
        column: 2
```

## Beispiel: gewähltes Helfer-Label

```yaml
ignored_helper_label:
  label_id: beispiel_pruefung_ignorieren
  name: Prüfung ignorieren
  available: true
ignored_helper_sources:
  - source_id: example_helper_entry_id
    helper: Gartenhaus Vergleich
```

Wird das gespeicherte Label später gelöscht, bleibt seine ID transparent, `name` wird `null`, `available` wird `false` und es werden keine Quellen dadurch ausgeschlossen.

## Status-Werte

| Status | Bedeutung |
|---|---|
| `ok` | vollständiger Scan, keine aktiven Funde |
| `missing_entities` | vollständiger Scan mit aktiven Funden |
| `partial_error` | mindestens eine Quelle konnte nicht geladen werden |
| `update_failed` | der gesamte Coordinator-Lauf ist fehlgeschlagen |
| `waiting` | Integration geladen, erster Scan steht noch aus |
