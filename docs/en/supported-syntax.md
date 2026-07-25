# Supported syntax

Template Entity Checker extracts **statically provable** entity references from Jinja templates. Templates are never rendered. The parser analyzes syntax, source positions, and local name bindings.

## Function calls

```jinja2
{{ states('sensor.living_room_example_temperature') }}
{{ state_attr('sensor.living_room_example_temperature', 'temperature') }}
{{ is_state('binary_sensor.patio_example_contact', 'on') }}
{{ is_state_attr('sensor.heating_example_status', 'mode', 'heating') }}
{{ has_value('sensor.garden_room_example_value') }}
```

## `has_value` as filter and test

Home Assistant supports three `has_value` forms, and all three are checked:

```jinja2
{{ has_value('sensor.garden_room_example_value') }}
{{ 'sensor.garden_room_example_value' | has_value }}
{{ 'sensor.garden_room_example_value' is has_value }}
{{ 'sensor.garden_room_example_value' is not has_value }}
```

Parenthesized string literals are supported as well. Dynamic operands produce a diagnostic, never a guessed finding.

```jinja2
{{ entity_variable | has_value }}
{{ entity_variable is has_value }}
```

## Dot notation

```jinja2
{{ states.sensor.living_room_example_temperature.state }}
{{ states.binary_sensor.patio_example_contact }}
```

## `expand()`

```jinja2
{{ expand(['sensor.living_room_example_temperature', 'sensor.basement_example_temperature']) }}
{{ expand('sensor.living_room_example_temperature', 'sensor.basement_example_temperature') }}
```

Literal entity IDs in lists, tuples, and multiple arguments are checked individually. In mixed containers, static elements are checked and the dynamic remainder produces exactly one diagnostic.

## Lookalikes intentionally ignored

The following are not static Home Assistant references:

- function names in plain text or Jinja comments
- text inside a string literal that merely looks like a call
- same-named methods on another object, such as `helper.expand(...)`
- macro names, filter-block names, and ordinary Jinja test names
- locally bound names that replace a global Home Assistant function

`has_value` is the deliberate exception for Jinja filters and tests because Home Assistant officially exposes those forms.

```jinja2
{# states('sensor.comment_example') #}
{{ "states('sensor.string_example')" }}
{{ helper.expand(['sensor.method_example']) }}
{{ expand(['sensor.real_example_finding']) }}
```

## Local variables and scopes

```jinja2
{{ states('sensor.before_binding_example') }}
{% set states = local_helper %}
{{ states('sensor.after_binding_example') }}
```

The first global call remains detectable. After the local binding, `states` is no longer treated as the Home Assistant function. A binding in a child scope does not hide a later global call outside that scope.

## Dynamic references

```jinja2
{{ states('sensor.' ~ room) }}
{{ state_attr(entity_variable, 'temperature') }}
{{ expand(['sensor.living_room_example_temperature', entity_variable]) }}
```

Dynamic IDs are not resolved. They produce `dynamic_entity_reference`, but never a fabricated missing entity.

## Duplicates and locations

Multiple occurrences of the same ID are grouped into one finding per helper, field, and reference. `occurrence_count` and every line and column position are preserved.
