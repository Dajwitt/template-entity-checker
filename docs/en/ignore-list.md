# Exclusions

> The searchable label selection described on this page belongs to the unreleased `0.1.3b1` preview. Public stable version `0.1.2` still shows a non-searchable list for this field.

Template Entity Checker provides two independent exclusions that can be combined. Both remain transparent in the sensor and diagnostics.

## Ignore an exact missing entity ID

Use **Exact entity IDs to ignore** when a specific target ID is intentionally allowed to be missing.

```text
sensor.garden_room_example_old_value
binary_sensor.workshop_example_old_contact
```

The searchable selection accepts multiple values. Current findings and previous values are offered. Because a missing ID may no longer exist in Home Assistant, any syntactically valid entity ID can also be entered manually.

### Rules

- complete entity IDs only
- no wildcards
- duplicates are removed
- the entity does not need to exist when settings are saved

## Ignore Template Helpers through a label

Use **Label for ignored Template Helpers** when every finding from selected helpers should be suppressed.

1. Create a freely named label in Home Assistant or reuse an existing one.
2. Assign it directly to the entity created by the Template Helper.
3. Search for and select that label in the Template Entity Checker options.

The label filters the **source**, not the missing target entity. Device and area labels are not inherited.

The selection is searchable, does not allow custom values, and saves at most one label. It offers current Home Assistant labels and, when necessary, the previously configured ID of a deleted label so it can be cleared.

### Per-finding partitioning

If a labeled and an unlabeled helper reference the same missing ID, the unlabeled helper's finding remains active. Only the labeled helper's finding moves to `ignored_matches`.

## Transparency

| Attribute | Contents |
|---|---|
| `missing_entities` | active, non-ignored findings |
| `ignored_entities` | configured exact ignore IDs |
| `ignored_helper_label` | label ID, current name, and availability |
| `ignored_helper_sources` | helpers actually excluded through the label |
| `ignored_matches` | findings suppressed by an exact ID or helper label |

### Example

| Entity | Source | Rule | Result |
|---|---|---|---|
| `sensor.garden_room_example_old_value` | any helper | exact ID | `ignored_matches` |
| `binary_sensor.workshop_example_old_contact` | labeled helper | helper label | `ignored_matches` |
| `binary_sensor.workshop_example_old_contact` | unlabeled helper | none | `missing_entities` |
