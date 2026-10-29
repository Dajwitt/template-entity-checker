# Requirements

## Runtime

| Requirement | Version/status |
|---|---|
| Home Assistant | 2026.7.3 or newer |
| HACS | current version for HACS installation |
| YAML configuration | neither required nor supported |

## Tested versions and installation channels

The minimum above is retained, not presented as the latest test baseline. Regular
tests use HA **2026.10.4** and pytest-homeassistant-custom-component **0.13.375**.
Type checking is isolated with compatible **2026.9.2** stubs and their required
September Core. The latest **2026.10.0** stubs introduce Coordinator/Probatio
type-contract errors in unchanged code. This retained pin is not the runtime
baseline and is never installed alongside the October test extra.
November **2026.11.0b0/b1** are tested separately with a real-Core harness, not the
incompatible October pytest plugin. Both November versions remain beta.

The candidate's three new helper types, exact field paths, ignore matches,
notification create/update/dismiss and options reload passed a targeted live b0
test. Browser rendering and Recorder persistence are not certified. The local
harness does not boot the complete HTTP/frontend/Recorder stack.

HACS and the built-in Marketplace in HA November beta are different installation
channels. Candidate installation through Marketplace was verified on b0 only;
read and accept its community-extension risk notice yourself. This is not a
blanket Marketplace certification or a requirement to switch away from HACS.

## Integration

| Property | Value |
|---|---|
| Integration type | `service` |
| IoT class | `local_polling` |
| Config Flow | yes |
| Config Entries | exactly one |
| Dependencies | `persistent_notification`, `template` |
| Platform | `sensor` |
| Expected entity | `sensor.template_entity_checker` |

## Languages

English and German user-interface translations are included.

## Release status

| Version | Status |
|---|---|
| `0.1.5` | version documented here |
| `0.1.4` | previous stable version |
