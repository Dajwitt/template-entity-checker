# Known limitations

## UI-created Template Helpers only

Templates from `configuration.yaml`, `templates.yaml`, packages, or other YAML files are **not** scanned. Home Assistant does not provide a stable public API for another integration to enumerate every original YAML template source.

## No rendering

Jinja is **not** rendered or semantically executed. Conservative static extraction detects only direct, statically provable references. Indirect references are intentionally not detected.

## Dynamic references

Dynamically constructed entity IDs cannot be resolved:

```jinja2
{{ states('sensor.' ~ variable) }}
{{ state_attr(entity_variable, 'attribute') }}
```

They produce parser diagnostics, never fabricated missing entities.

## Internal Template Helper schema

The public Config Entry API is used read-only, but the `template` integration's option-field structure is an internal schema that may change with Home Assistant releases. Access is isolated in `template_sources.py` and tested. Unknown newer schema versions produce source loading errors instead of being guessed.

## Other sources are not scanned

Templates in automations, scripts, scenes, dashboards, blueprints, and other integrations are not scanned.

## No repair

The integration reports problems but never changes or repairs references.

## State attribute size

Very large result sets can approach Home Assistant's state attribute size limits. Export and Repairs integration are future work.

## Not considered missing

- `unavailable` entities with a registry entry
- `unknown` entities with a registry entry
- disabled entities with a registry entry
- entities without a current state but with a registry entry
