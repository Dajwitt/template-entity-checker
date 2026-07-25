# Events

## `template_entity_checker_result_changed`

After the first complete scan establishes a baseline, the integration fires this event whenever the structured active `missing_entities` findings change.

### When does it fire?

| Condition | Fires? |
|---|---|
| Result changes after the baseline | yes |
| Result stays identical | no |
| One or more sources fail to load | no |
| First complete scan establishes the baseline | no |

### Event data

| Field | Type | Description |
|---|---|---|
| `previous_count` | int | previous number of missing entity IDs |
| `current_count` | int | current number of missing entity IDs |
| `added_entities` | list | newly missing entity IDs, sorted |
| `removed_entities` | list | entity IDs that are no longer missing, sorted |
| `missing_entities` | dict | complete current finding structure |
| `scan_time` | string | ISO scan timestamp |

### Event trigger example

```yaml
automation:
  - alias: "Template findings changed"
    trigger:
      - platform: event
        event_type: template_entity_checker_result_changed
    action:
      - action: persistent_notification.create
        data:
          title: "Template check updated"
          message: >
            {{ trigger.event.data.previous_count }} →
            {{ trigger.event.data.current_count }} missing entities.
            Added: {{ trigger.event.data.added_entities | join(', ') }}
```

### Only react to new findings

```yaml
automation:
  - alias: "New missing Template entities"
    trigger:
      - platform: event
        event_type: template_entity_checker_result_changed
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.added_entities | length > 0 }}"
    action:
      - action: persistent_notification.create
        data:
          title: "New missing entities"
          message: "{{ trigger.event.data.added_entities | join(', ') }}"
```
