# Troubleshooting

## Sensor shows `waiting`

The first scan starts only after Home Assistant is fully running. `waiting` is normal shortly after a restart. Wait briefly or call `template_entity_checker.scan_now`.

## `load_errors` contains entries

At least one Template source could not be loaded safely.

1. Review `load_errors` and `last_error` in the sensor.
2. Confirm that the named Template Helper still exists.
3. After a Home Assistant update, check whether the Config Entry uses a newer, unconfirmed schema version.
4. Start another scan.

A partial run does not dismiss an existing notification or establish a new event baseline.

## `parser_diagnostics` contains entries

| Code | Meaning |
|---|---|
| `dynamic_entity_reference` | entity ID is dynamic and cannot be proven statically |
| `invalid_static_entity_id` | static value is not a valid entity ID |
| `template_syntax_error` | Jinja syntax is invalid |

A dynamic diagnostic does not necessarily mean the template is broken. The checker deliberately does not guess the ID.

## A missing entity is not reported

Possible reasons:

1. It still has an Entity Registry entry.
2. Its exact ID is listed in `ignored_entities`; review `ignored_matches`.
3. The finding comes from a helper carrying the selected ignore label; review `ignored_helper_sources` and `ignored_matches`.
4. The reference is dynamic; review `parser_diagnostics`.
5. The template comes from YAML, an automation, script, dashboard, or another unsupported source.

## The helper label does not work

- Assign the label directly to the entity created by the Template Helper.
- Device and area labels are not inherited.
- Check `ignored_helper_label.available`.
- After the stored label is deleted, no source is excluded through it by design.

## A stored label is shown only as an ID

The label was probably deleted. Open the options and remove the old selection or choose an existing label. The scan continues conservatively without label-based exclusions.

## No notification appears

- Notifications must be enabled.
- `missing_entities` must contain active findings; ignored findings alone do not create a notification.
- A partial scan leaves the current notification unchanged.
- An identical complete result does not create a duplicate.

## Reporting a problem

1. Confirm the latest public version is installed.
2. Run `template_entity_checker.scan_now`.
3. Review the sensor attributes and [Diagnostics](./diagnostics.md).
4. Provide reproduction steps and sanitized diagnostics in a GitHub issue.

Never publish credentials, private URLs, or personal data.
