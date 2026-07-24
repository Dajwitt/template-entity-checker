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


@pytest.mark.parametrize(
    "template",
    [
        "Plain text expand(['sensor.text']) and has_value('sensor.text')",
        "{# expand(['sensor.comment']) and has_value('sensor.comment') #}",
        "{{ \"expand(['sensor.string'])\" }}",
        "{{ helper.expand(['sensor.member']) }}",
        "{{ helper.has_value('sensor.member') }}",
        "{# states.sensor.comment #}",
        "{{ helper.states.sensor.member }}",
    ],
)
def test_non_global_or_non_executable_references_are_ignored(template):
    assert parse_template(template) == ([], [])


def test_real_global_calls_after_decoys_are_still_detected():
    template = (
        "{# expand(['sensor.comment']) #} "
        "{{ \"has_value('sensor.string')\" }} "
        "{{ expand(['sensor.real_expand']) }} "
        "{{ has_value('binary_sensor.real_value') }}"
    )

    references, diagnostics = parse_template(template)

    assert [item.entity_id for item in references] == [
        "sensor.real_expand",
        "binary_sensor.real_value",
    ]
    assert diagnostics == []


def test_crlf_templates_keep_references_and_positions():
    template = (
        "prefix\r\n"
        "{{ states('sensor.after_crlf') }}\r\n"
        "{{ expand([\r\n"
        "  'sensor.expand_after_crlf'\r\n"
        "]) }}\r\n"
        "{{ states.binary_sensor.dotted_after_crlf }}"
    )

    references, diagnostics = parse_template(template)

    assert [item.entity_id for item in references] == [
        "sensor.after_crlf",
        "sensor.expand_after_crlf",
        "binary_sensor.dotted_after_crlf",
    ]
    assert [item.line for item in references] == [2, 3, 6]
    assert "\r\n" in references[1].reference
    assert diagnostics == []


@pytest.mark.parametrize(
    "template",
    [
        (
            "{% set states = helper %}"
            "{{ states('sensor.fake') }}"
            "{{ states.sensor.other }}"
        ),
        "{% macro m(expand) %}{{ expand(['sensor.fake']) }}{% endmacro %}",
        ("{% for has_value in values %}{{ has_value('sensor.fake') }}{% endfor %}"),
        "{% macro states(value) %}x{% endmacro %}{{ states('sensor.fake') }}",
        "{% import 'helpers.jinja' as expand %}{{ expand(['sensor.fake']) }}",
        (
            "{% from 'helpers.jinja' import check as has_value %}"
            "{{ has_value('sensor.fake') }}"
        ),
    ],
)
def test_locally_bound_home_assistant_names_are_not_treated_as_globals(template):
    assert parse_template(template) == ([], [])


@pytest.mark.parametrize(
    ("template", "expected_entity"),
    [
        (
            "{{ states('sensor.before_set') }}{% set states = helper %}",
            "sensor.before_set",
        ),
        (
            "{{ states.sensor.before_set }}{% set states = helper %}",
            "sensor.before_set",
        ),
        (
            "{{ expand(['sensor.before_macro']) }}"
            "{% macro expand(value) %}{{ expand(value) }}{% endmacro %}",
            "sensor.before_macro",
        ),
    ],
)
def test_global_calls_before_same_scope_bindings_are_preserved(
    template, expected_entity
):
    references, diagnostics = parse_template(template)

    assert [item.entity_id for item in references] == [expected_entity]
    assert diagnostics == []


def test_assignment_value_is_evaluated_before_its_target_is_bound():
    references, diagnostics = parse_template(
        "{% set states = states('sensor.assignment_value') %}"
    )

    assert [item.entity_id for item in references] == ["sensor.assignment_value"]
    assert diagnostics == []


def test_bindings_apply_in_source_order_inside_if_branches():
    template = (
        "{% if true %}"
        "{{ states('sensor.before_branch_set') }}"
        "{% set states = helper %}"
        "{{ states('sensor.after_branch_set') }}"
        "{% endif %}"
    )

    references, diagnostics = parse_template(template)

    assert [item.entity_id for item in references] == ["sensor.before_branch_set"]
    assert diagnostics == []


def test_for_target_is_not_bound_in_else_branch():
    template = (
        "{% for states in [] %}"
        "{{ states('sensor.inside_loop') }}"
        "{% else %}"
        "{{ states('sensor.loop_else') }}"
        "{% endfor %}"
    )

    references, diagnostics = parse_template(template)

    assert [item.entity_id for item in references] == ["sensor.loop_else"]
    assert diagnostics == []


@pytest.mark.parametrize(
    ("template", "expected_entity"),
    [
        (
            "{% for states in values %}"
            "{{ states('sensor.inside_loop') }}"
            "{% endfor %}"
            "{{ states('sensor.after_loop') }}",
            "sensor.after_loop",
        ),
        (
            "{% macro check(expand) %}"
            "{{ expand(['sensor.inside_macro']) }}"
            "{% endmacro %}"
            "{{ expand(['sensor.after_macro']) }}",
            "sensor.after_macro",
        ),
        (
            "{% with has_value = helper %}"
            "{{ has_value('sensor.inside_with') }}"
            "{% endwith %}"
            "{{ has_value('sensor.after_with') }}",
            "sensor.after_with",
        ),
    ],
)
def test_scoped_bindings_do_not_hide_later_global_calls(template, expected_entity):
    references, diagnostics = parse_template(template)

    assert [item.entity_id for item in references] == [expected_entity]
    assert diagnostics == []


def test_scoped_states_binding_does_not_hide_later_dotted_reference():
    template = (
        "{% for states in values %}"
        "{{ states.sensor.inside_loop }}"
        "{% endfor %}"
        "{{ states.sensor.after_loop }}"
    )

    references, diagnostics = parse_template(template)

    assert [item.entity_id for item in references] == ["sensor.after_loop"]
    assert diagnostics == []


def test_filter_block_binding_does_not_hide_later_global_call():
    template = (
        "{% filter upper %}"
        "{% set states = helper %}"
        "{{ states('sensor.inside_filter') }}"
        "{% endfilter %}"
        "{{ states('sensor.after_filter') }}"
    )

    references, diagnostics = parse_template(template)

    assert [item.entity_id for item in references] == ["sensor.after_filter"]
    assert diagnostics == []


def test_filter_block_body_bindings_follow_execution_order():
    template = (
        "{% filter replace(states('sensor.filter_argument'), 'x') %}"
        "{{ states('sensor.before_filter_set') }}"
        "{% set states = helper %}"
        "{% endfilter %}"
    )

    references, diagnostics = parse_template(template)

    assert [item.entity_id for item in references] == ["sensor.before_filter_set"]
    assert diagnostics == []


def test_filter_block_name_does_not_consume_later_call_permission():
    template = (
        "{% filter states('sensor.filter_arg') %}x{% endfilter %}"
        "{{ states('sensor.real') }}"
    )

    references, diagnostics = parse_template(template)

    assert [item.entity_id for item in references] == ["sensor.real"]
    assert diagnostics == []


def test_dotted_filter_block_name_does_not_consume_later_permission():
    template = (
        "{% filter states.sensor.filter_arg %}x{% endfilter %}{{ states.sensor.real }}"
    )

    references, diagnostics = parse_template(template)

    assert [item.entity_id for item in references] == ["sensor.real"]
    assert diagnostics == []


@pytest.mark.parametrize(
    "template",
    [
        "{{ 'x' | states.sensor.fake }}{{ states.sensor.real }}",
        "{% set captured | states.sensor.fake %}x{% endset %}{{ states.sensor.real }}",
    ],
)
def test_dotted_filter_name_does_not_consume_later_permission(template):
    references, diagnostics = parse_template(template)

    assert [item.entity_id for item in references] == ["sensor.real"]
    assert diagnostics == []


def test_macro_name_does_not_consume_default_call_permission():
    template = (
        "{% macro states(x=states('sensor.default')) %}"
        "{{ states('sensor.self') }}"
        "{% endmacro %}"
    )

    references, diagnostics = parse_template(template)

    assert [item.entity_id for item in references] == ["sensor.default"]
    assert diagnostics == []


def test_assign_block_body_bindings_follow_source_order():
    template = (
        "{% set captured %}"
        "{% set states = helper %}"
        "{{ states('sensor.local') }}"
        "{% endset %}"
        "{{ states('sensor.real') }}"
    )

    references, diagnostics = parse_template(template)

    assert [item.entity_id for item in references] == ["sensor.real"]
    assert diagnostics == []


def test_filtered_assign_block_uses_final_body_scope_for_filter():
    template = (
        "{% set captured | replace(states('sensor.filter_arg'), 'x') %}"
        "{% set states = helper %}"
        "{{ states('sensor.local') }}"
        "{% endset %}"
        "{{ states('sensor.real') }}"
    )

    references, diagnostics = parse_template(template)

    assert [item.entity_id for item in references] == ["sensor.real"]
    assert diagnostics == []


def test_conditional_binding_conservatively_hides_later_same_scope_call():
    template = (
        "{% if condition %}{% set states = helper %}{% endif %}"
        "{{ states('sensor.after_conditional_set') }}"
    )

    assert parse_template(template) == ([], [])


def test_call_block_parameters_stay_scoped_to_the_caller_body():
    template = (
        "{% macro wrapper() %}{{ caller() }}{% endmacro %}"
        "{% call(states=states('sensor.call_default')) wrapper() %}"
        "{{ states('sensor.inside_call') }}"
        "{% endcall %}"
        "{{ states('sensor.after_call') }}"
    )

    references, diagnostics = parse_template(template)

    assert [item.entity_id for item in references] == [
        "sensor.call_default",
        "sensor.after_call",
    ]
    assert diagnostics == []


def test_block_binding_does_not_hide_later_global_call():
    template = (
        "{% block content %}"
        "{% set states = helper %}"
        "{{ states('sensor.inside_block') }}"
        "{% endblock %}"
        "{{ states('sensor.after_block') }}"
    )

    references, diagnostics = parse_template(template)

    assert [item.entity_id for item in references] == ["sensor.after_block"]
    assert diagnostics == []


@pytest.mark.parametrize(
    "template",
    [
        "{{ value is states('sensor.test_call') }}",
        "{{ value is not states('sensor.negated_test_call') }}",
        "{{ value is expand(['sensor.test_expand']) }}",
        "{{ value is not expand(['sensor.negated_test_expand']) }}",
        "{{ value is states.sensor.test_dotted }}",
        "{{ value is not states.sensor.negated_test_dotted }}",
    ],
)
def test_jinja_tests_are_not_treated_as_home_assistant_globals(template):
    assert parse_template(template) == ([], [])


def test_jinja_test_does_not_hide_later_global_call_on_same_line():
    template = (
        "{{ value is not states('sensor.test_call') }}{{ states('sensor.real_call') }}"
    )

    references, diagnostics = parse_template(template)

    assert [item.entity_id for item in references] == ["sensor.real_call"]
    assert diagnostics == []


def test_tokens_never_form_calls_across_jinja_block_boundaries():
    assert parse_template("{{ states }} {{ ('sensor.fake') }}") == ([], [])
    assert parse_template("{{ expand }} {{ (['sensor.fake']) }}") == ([], [])


def test_home_assistant_loop_control_syntax_does_not_block_later_references():
    template = (
        "{% for item in [] %}{% break %}{% endfor %}{{ states('sensor.after_break') }}"
    )

    references, diagnostics = parse_template(template)

    assert [item.entity_id for item in references] == ["sensor.after_break"]
    assert diagnostics == []


def test_has_value_literal_is_static_reference():
    references, diagnostics = parse_template(
        "{{ has_value('binary_sensor.example_missing') }}"
    )

    assert [item.entity_id for item in references] == ["binary_sensor.example_missing"]
    assert diagnostics == []


def test_has_value_variable_is_dynamic_and_never_guessed():
    references, diagnostics = parse_template("{{ has_value(entity_var) }}")

    assert references == []
    assert [item.code for item in diagnostics] == ["dynamic_entity_reference"]


@pytest.mark.parametrize(
    "expression",
    [
        "{{ states('sensor.example' ~ suffix) }}",
        "{{ has_value('sensor.example' ~ suffix) }}",
    ],
)
def test_valid_entity_prefix_with_concatenation_remains_dynamic(expression):
    references, diagnostics = parse_template(expression)

    assert references == []
    assert [item.code for item in diagnostics] == ["dynamic_entity_reference"]


def test_has_value_invalid_literal_gets_diagnostic():
    references, diagnostics = parse_template("{{ has_value('Not An Entity') }}")

    assert references == []
    assert [item.code for item in diagnostics] == ["invalid_static_entity_id"]


@pytest.mark.parametrize(
    ("expression", "expected_entities"),
    [
        (
            "{{ expand(['media_player.example_one', 'media_player.example_two']) }}",
            ["media_player.example_one", "media_player.example_two"],
        ),
        (
            "{{ expand('sensor.zeta', 'sensor.alpha') }}",
            ["sensor.zeta", "sensor.alpha"],
        ),
        (
            "{{ expand(('switch.example_one', 'switch.example_two')) }}",
            ["switch.example_one", "switch.example_two"],
        ),
    ],
)
def test_expand_static_containers_yield_each_reference(expression, expected_entities):
    references, diagnostics = parse_template(expression)

    assert [item.entity_id for item in references] == expected_entities
    assert diagnostics == []


def test_expand_mixed_list_keeps_static_part_and_diagnoses_dynamic_part():
    references, diagnostics = parse_template(
        "{{ expand(['sensor.example', entity_var]) }}"
    )

    assert [item.entity_id for item in references] == ["sensor.example"]
    assert [item.code for item in diagnostics] == ["dynamic_entity_reference"]


def test_expand_invalid_literal_keeps_valid_part_and_reports_invalid_part():
    references, diagnostics = parse_template(
        "{{ expand(['sensor.example', 'Not An Entity']) }}"
    )

    assert [item.entity_id for item in references] == ["sensor.example"]
    assert [item.code for item in diagnostics] == ["invalid_static_entity_id"]


def test_expand_multiline_list_uses_call_start_position():
    references, diagnostics = parse_template(
        "{% set marker = true %}\n"
        "{{ expand([\n"
        "  'sensor.example_one',\n"
        "  'sensor.example_two'\n"
        "]) }}"
    )

    assert [item.entity_id for item in references] == [
        "sensor.example_one",
        "sensor.example_two",
    ]
    assert diagnostics == []
    assert all((item.line, item.column) == (2, 4) for item in references)


def test_expand_duplicate_literals_preserve_each_occurrence():
    references, diagnostics = parse_template(
        "{{ expand(['sensor.same', 'sensor.same']) }}"
    )

    assert [item.entity_id for item in references] == ["sensor.same", "sensor.same"]
    assert diagnostics == []


def test_expand_concatenated_argument_is_dynamic_and_never_guessed():
    references, diagnostics = parse_template("{{ expand('sensor.' ~ object_id) }}")

    assert references == []
    assert [item.code for item in diagnostics] == ["dynamic_entity_reference"]
