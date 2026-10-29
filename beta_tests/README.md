# Home Assistant November beta compatibility tests

Included in integration 0.1.5; Template Config Entry schema 2.1 is unchanged.
The allowlist adds these real TemplateSelector fields:

- climate: `hvac_modes`, `hvac_mode`, `hvac_action`, `current_temperature`, `target_temperature`.
- media_player: `state`, `volume_level`, `is_volume_muted`, `source`, `source_list`.
- water_heater: `operation_list`, `operation_mode`, `current_temperature`, `target_temperature`, plus `additional_options.away_mode`.
- Shared `additional_options.availability` remains supported. Actions, unknown fields,
  wrong containers and unconfirmed schema versions remain excluded/rejected.

## Reproduce locally

From the repository root, with uv and Python 3.14.2 or newer. Use new environment
and output paths; do not overwrite an existing environment. Repeat with b1:

```sh
uv venv .venv-beta-b0 --python 3.14.2
uv pip install --python .venv-beta-b0/bin/python 'homeassistant==2026.11.0b0' 'pytest==9.2.0' 'pytest-asyncio==1.4.1' 'pytest-cov==7.1.0'
.venv-beta-b0/bin/python -B beta_tests/run.py ../beta-evidence-b0
uv pip check --python .venv-beta-b0/bin/python
```

The runner rejects other Core versions, disables plugin autoload, explicitly loads
pytest-asyncio, and copies the three current pure regression modules unchanged to
an isolated directory outside `tests/conftest.py`. It tests the checked-out
integration, including the real integration loader's custom_components path.
Output includes environment/command, JUnit, final log and synthetic diagnostics.
Keep these generated artifacts outside the public Git tree.

## Actual candidate results (2026-10-29)

Python 3.14.2; pytest 9.2.0; pytest-asyncio 1.4.1; Probatio 0.13.0.

| Core | Pure regressions | Core harness | Combined result |
| --- | ---: | ---: | --- |
| 2026.11.0b0 | 166 | 24 | 190 passed, 1 warning, 88.15 s |
| 2026.11.0b1 | 166 | 24 | 190 passed, 1 warning, 85.61 s |

These are two runs of the same tests, not 380 distinct cases. All 20 installed
Template helper schemas and exact field paths matched. One upstream aiohttp
HomeAssistantApplication deprecation warning occurred per run. Relative interpreter
paths also emitted sys.prefix startup warnings; neither run failed.

The complete regular suite separately passed against the existing synchronized
HA 2026.9.2 environment: 200 passed, 94.66% coverage (gate 90%). Ruff, format,
mypy, legacy-reference and diff checks passed. These are historical candidate
results, not the current stable test baseline. Additionally, a fresh environment
from the then-published lock (HA 2026.7.3) passed the complete
200-test suite with 94.66% coverage in 4.69 s.

## Boundaries

No full unchanged project-suite claim under November: the available
pytest-homeassistant-custom-component 0.13.375 pins HA 2026.10.4 and was not forced
into either beta environment. No dependency overrides or invented November stubs.

The harness uses real Core flow/registry/coordinator/sensor/notification APIs,
real reload/unload and real 62-second polling. ConfigEntries are synthetic,
disabled source fixtures, not live user helpers. Dependency components are marked
ready; no HTTP/frontend/recorder stack, actual template rendering or complete
Core boot is tested. This harness alone does not certify live-instance, browser,
Marketplace-installation or Recorder behavior. A separate targeted live test on
b0 passed all three new types, field paths, ignore matches, notification lifecycle
and options reload; browser rendering and Recorder persistence remain outside
that acceptance. The regular suite now targets HA 2026.10.4 with plugin 0.13.375;
type checking runs separately with compatible 2026.9.2 stubs and September Core.
The latest 2026.10.0 stubs cause Coordinator/Probatio type-contract errors in
unchanged code; this retained typing pin is not the runtime test baseline.
Both November versions are beta.
