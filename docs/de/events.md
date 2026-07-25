# Events

## `template_entity_checker_result_changed`

Nach dem ersten vollständigen Scan, der eine Baseline etabliert, feuert die Integration ein Event, sobald sich die strukturierte Menge der aktiven `missing_entities` ändert.

### Wann wird gefeuert?

| Bedingung | feuert? |
|---|---|
| Ergebnis ändert sich nach Baseline | ja |
| Ergebnis unverändert | nein |
| Partielles Quell-Laden fehlgeschlagen | nein |
| Erster Scan (Baseline-Erstellung) | nein |

### Event-Daten

| Feld | Typ | Beschreibung |
|---|---|---|
| `previous_count` | int | Anzahl fehlender Entities vorher |
| `current_count` | int | Anzahl fehlender Entities aktuell |
| `added_entities` | list | Neu hinzugekommene Entity-IDs (sortiert) |
| `removed_entities` | list | Nicht mehr fehlende Entity-IDs (sortiert) |
| `missing_entities` | dict | Aktuelles vollständiges Ergebnis |
| `scan_time` | string | ISO-Zeitstempel des Scans |

### Beispiel: Event-Trigger

```yaml
automation:
  - alias: "Fehlende Template-Entities geändert"
    trigger:
      - platform: event
        event_type: template_entity_checker_result_changed
    action:
      - action: persistent_notification.create
        data:
          title: "Template-Check aktualisiert"
          message: >
            {{ trigger.event.data.previous_count }} →
            {{ trigger.event.data.current_count }} fehlende Entities.
            Neu: {{ trigger.event.data.added_entities | join(', ') }}
```

### Beispiel: Nur bei neuen Entities

```yaml
automation:
  - alias: "Neue fehlende Template-Entities"
    trigger:
      - platform: event
        event_type: template_entity_checker_result_changed
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.added_entities | length > 0 }}"
    action:
      - action: persistent_notification.create
        data:
          title: "Neue fehlende Entities"
          message: "{{ trigger.event.data.added_entities | join(', ') }}"
```