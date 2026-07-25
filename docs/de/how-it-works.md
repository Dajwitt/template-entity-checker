# Funktionsweise

## Scan-Prozess

```text
Home Assistant vollständig gestartet
        │
        ▼
UI-Template-Helfer über Config Entries laden
        │
        ▼
bestätigte Template-Felder extrahieren
        │
        ▼
Jinja statisch parsen, niemals rendern
        │
        ▼
Referenzen gegen State Machine und Entity Registry prüfen
        │
        ▼
exakte Ignore-IDs und direktes Helfer-Label fundweise anwenden
        │
        ▼
Sensor aktualisieren
Benachrichtigung bei geändertem vollständigem Ergebnis anpassen
Event bei geändertem vollständigem Ergebnis feuern
```

## Template-Helfer laden

Die Integration nutzt Home Assistants öffentliche Config-Entry-API nur lesend.

- kein direkter `.storage`-Zugriff
- kein Rendern oder Ausführen von Templates
- nur bestätigte `TemplateSelector`-Felder
- bestätigtes Schema 1.0 bis 1.2
- neuere oder unbekannte Schemata werden als `load_errors` gemeldet, nicht geraten

## Unterstützte Template-Helfer-Typen

| Typ | Gescannte Stammfelder |
|---|---|
| `alarm_control_panel` | `value_template` |
| `binary_sensor` | `state` |
| `button` | keine Stammfelder |
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

Bei allen Typen wird zusätzlich `advanced_options.availability` geprüft. Beim `device_tracker` kommt `advanced_options.location_accuracy` hinzu. Nicht vorhandene Felder zählen nicht als Quelle; vorhandene leere Felder werden dagegen als gescannte Quelle gezählt.

## Wann gilt eine Entity als fehlend?

Eine Entity wird nur gemeldet, wenn sie weder in der State Machine noch in der Entity Registry existiert. `unavailable`, `unknown`, deaktiviert oder momentan ohne State gilt nicht als fehlend, solange ein Registry-Eintrag vorhanden ist.

## Ausschlüsse

Exakte Ignore-IDs unterdrücken alle Funde dieser Ziel-ID. Das optionale Helfer-Label wird direkt an den von Template-Helfern erzeugten Entities ausgewertet und unterdrückt nur Funde der betroffenen Quellen. Beide Wege werden nach `ignored_matches` verschoben.

## Automatischer und manueller Scan

Nach dem vollständigen Start führt die Integration den ersten Scan aus. Danach scannt sie im konfigurierten Intervall. Die Aktion `template_entity_checker.scan_now` fordert einen sofortigen Lauf an. Ein Async-Lock verhindert parallele Scans; ein weiterer Auslöser wartet.

## Partielles Fehlschlagen

Ladefehler einzelner Quellen führen zu `partial_error`. Erfolgreich geladene Quellen bleiben im Sensor sichtbar. Ein unvollständiger Lauf verändert weder die bestehende Benachrichtigung noch die Ergebnis-Baseline für Events.

## Gruppierung

Funde werden nach Entity-ID gruppiert. Je Helfer, Feld und Referenz bleiben Helfername, Typ, Quell-ID, Originalreferenz, Vorkommenszahl sowie alle Zeilen- und Spaltenpositionen erhalten.
