"""Tests for conservative static parsing."""

import pytest

from custom_components.template_entity_checker.parser import parse_template


@pytest.mark.parametrize(
    ("expression", "entity_id"),
    [
        ("{{ states('sensor.example') }}", "sensor.example"),
        ('{{ state_attr("sensor.example", "unit") }}', "sensor.example"),
        ("{{ is_state('binary_sensor.example', 'on') }}", "binary_sensor.example"),
        (
            "{{ is_state_attr('sensor.example', 'mode', 'auto') }}",
            "sensor.example",
        ),
        ("{{ states.sensor.example.state }}", "sensor.example"),
        ("{{ states.binary_sensor.example }}", "binary_sensor.example"),
        ("{{ expand('group.example') | list }}", "group.example"),
    ],
)
def test_supported_static_patterns(expression, entity_id):
    """Every promised static syntax yields exactly its literal ID."""
    references, diagnostics = parse_template(expression)
    assert [item.entity_id for item in references] == [entity_id]
    assert diagnostics == []


def test_dynamic_reference_is_diagnostic_and_never_guessed():
    """A concatenated ID produces no synthetic missing candidate."""
    references, diagnostics = parse_template("{{ states('sensor.' ~ variable) }}")
    assert references == []
    assert [item.code for item in diagnostics] == ["dynamic_entity_reference"]
    assert "sensor.variable" not in repr(diagnostics)


def test_variable_first_argument_is_dynamic():
    references, diagnostics = parse_template("{{ state_attr(entity_var, 'x') }}")
    assert references == []
    assert diagnostics[0].code == "dynamic_entity_reference"


def test_partial_template_keeps_safe_matches_and_diagnostic():
    template = "{{ states('sensor.safe') }} + {{ states(entity_var) }}"
    references, diagnostics = parse_template(template)
    assert [item.entity_id for item in references] == ["sensor.safe"]
    assert diagnostics[0].code == "dynamic_entity_reference"


def test_duplicate_occurrences_are_preserved_with_positions():
    references, _ = parse_template(
        "{{ states('sensor.same') }}\n{{ states('sensor.same') }}"
    )
    assert len(references) == 2
    assert [item.line for item in references] == [1, 2]
    assert all(item.column == 4 for item in references)


def test_invalid_literal_gets_diagnostic():
    references, diagnostics = parse_template("{{ states('Not An Entity') }}")
    assert references == []
    assert diagnostics[0].code == "invalid_static_entity_id"


def test_non_reference_text_is_ignored():
    assert parse_template("{{ 1 + 1 }}") == ([], [])
