# Template Entity Checker

**Documentation version: 0.1.5** · Home Assistant custom integration

Template Entity Checker scans Template Helpers created through the Home Assistant user interface for static entity references that no longer exist.

The integration reads Template Helpers through the public Config Entry API. It **never** renders or changes templates, repairs references, guesses dynamic entity IDs, or reads or writes `.storage` files.

## Scope

**UI-created Template Helpers only.** Templates from `configuration.yaml`, `templates.yaml`, packages, or other YAML files are not scanned.

## New in 0.1.5

- 20 confirmed UI Template Helper types, adding `climate`, `media_player` and `water_heater`, including `additional_options.away_mode`
- compatibility tested against HA `2026.11.0b0` and `2026.11.0b1`; Home Assistant November remains beta, while this integration release is regular
- schema `2.1` and the UI-only/action-exclusion boundaries remain unchanged; see [tested versions and limits](./requirements.md)

## New in 0.1.4

- support for Home Assistant 2026.8 Template Helper Config Entry schema `2.1`
- large live finding details are no longer stored in Recorder history, while compact scan history remains available

## New in 0.1.3

- searchable selection for the optional helper label; custom values are blocked, a previously saved deleted label ID remains visible so it can be cleared, and at most one label can be saved

## New in 0.1.2

- `has_value` as a function, filter, and Jinja test
- searchable multi-select for exact ignored entity IDs, while still allowing free entry of missing IDs
- optional source-level exclusion using one freely selected Home Assistant label
- transparent details about the effective label, ignored helpers, and ignored findings
- native on/off control for persistent notifications

## Quick start

1. [Install](./installation.md) through HACS
2. [Configure](./configuration.md) under **Settings → Devices & services**
3. [Review results](./sensor.md) through `sensor.template_entity_checker`

## Documentation

| Section | Contents |
|---|---|
| [Installation](./installation.md) | HACS and manual installation |
| [Configuration](./configuration.md) | Config Flow, Options Flow, and settings |
| [How it works](./how-it-works.md) | Scan process and Template Helper types |
| [Supported syntax](./supported-syntax.md) | Static Jinja references with examples |
| [Result sensor](./sensor.md) | State and attributes |
| [Action](./services.md) | `template_entity_checker.scan_now` |
| [Events](./events.md) | `template_entity_checker_result_changed` |
| [Notifications](./notifications.md) | Persistent notification behavior |
| [Exclusions](./ignore-list.md) | Exact IDs and helper labels |
| [Diagnostics](./diagnostics.md) | Diagnostics download and contents |
| [Known limitations](./limitations.md) | What cannot be resolved |
| [Troubleshooting](./troubleshooting.md) | Narrow down common problems |
| [Requirements](./requirements.md) | Versions and platforms |
