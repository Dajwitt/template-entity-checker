# Notifications

When notifications are enabled, the integration manages one persistent notification.

## Behavior

- one fixed notification ID, so repeated scans do not create duplicates
- only a changed complete result updates the notification
- identical results do not create another notification
- findings are grouped by Template Helper
- a clean complete scan dismisses the notification
- disabling notifications dismisses it as well
- ignored findings alone do not create a notification

## Partial failures

A partial source loading failure leaves the existing notification unchanged. Incomplete input must not hide a real problem.

## Example notification

```text
Template Entity Checker: 2 missing entities

**Template Helpers**

Average humidity
• sensor.living_room_docs_old_value
• sensor.basement_docs_old_value

Complete list: sensor attribute `missing_entities`
```

## Language

The title and message follow Home Assistant's configured language. English and German are supported.
