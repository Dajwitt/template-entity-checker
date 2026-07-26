# Configuration

Initial setup and later changes use Home Assistant's Config Flow and Options Flow. YAML configuration is neither required nor supported.

> This page documents the unreleased `0.1.3b1` preview. The public stable version `0.1.2` does not include searchable label selection yet.

## Initial setup

After installation and restart:

1. Open **Settings → Devices & services**.
2. Select **Add integration**.
3. Search for **Template Entity Checker**.
4. Set the scan interval in minutes (default: 15).
5. Enable or disable persistent notifications.
6. Optionally select exact entity IDs to ignore or freely enter missing IDs.
7. Optionally search for and select a Home Assistant label to ignore complete Template Helper sources.

## Settings

| Field | Type | Default | Description |
|---|---|---|---|
| Scan interval | integer (1–1440) | 15 minutes | Time between automatic scans |
| Notifications | on/off | on | Persistent notification for active findings |
| Exact entity IDs to ignore | searchable multi-select with custom values | empty | Suppresses the selected missing target IDs completely |
| Label for ignored Template Helpers | searchable selection without custom values, at most one | empty | Suppresses findings from helpers whose generated entity directly carries this label |

## Searchable entity selection

The Options Flow offers:

- currently reported missing entity IDs,
- findings that were previously ignored,
- already configured ignore IDs.

A truly missing entity may no longer exist in the Entity Registry, so any syntactically valid entity ID can still be entered manually.

## Excluding helpers through a label

The optional label is selected from Home Assistant's current Label Registry and stored by its stable label ID.

- The selection is searchable and does not allow custom values. It offers current labels and, when necessary, the previously configured ID of a deleted label so it can be cleared.
- At most one label can be saved.
- Assign the label directly to the entity created by the Template Helper.
- Device and area labels are not inherited.
- Renaming the label does not break the exclusion.
- If the stored label is deleted, no helper remains excluded through it; the scan stays complete and reports the label as unavailable.
- Exact IDs and the label exclusion can be used together.

## Options Flow

Change all fields under **Settings → Devices & services → Template Entity Checker → Configure**. Saving reloads the integration and applies the new settings to the next scan.

## Single instance and migration

Only one integration instance is supported. A second setup attempt is aborted.

Version 1 Config Entries are migrated automatically to version 2. The retired Template Helper type selection is removed from data and options; all confirmed types are scanned automatically. Legacy text-based ignore values remain readable and are converted to the new list the next time settings are saved.

## Intentional limits

- no wildcards such as `sensor.living_room_*`
- no selection of individual Template Helper types
- no dashboard selection
- no YAML configuration
