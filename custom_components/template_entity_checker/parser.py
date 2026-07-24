"""Conservative static parser for Home Assistant Jinja entity references."""

from __future__ import annotations

import re

from jinja2 import Environment, TemplateSyntaxError, nodes

from .models import ParserDiagnostic, StaticReference

_ENTITY = r"[a-z_][a-z0-9_]*\.[a-z0-9_]+"
_DIRECT_FUNCTIONS = {
    "states",
    "state_attr",
    "is_state",
    "is_state_attr",
    "has_value",
}
_SUPPORTED_FUNCTIONS = _DIRECT_FUNCTIONS | {"expand"}
_JINJA_ENVIRONMENT = Environment(
    autoescape=True,
    extensions=["jinja2.ext.loopcontrols", "jinja2.ext.do"],
)

# token_type, token_value, normalized source offset, Jinja region number
_LocatedToken = tuple[str, str, int, int]


def parse_template(
    template: str,
) -> tuple[list[StaticReference], list[ParserDiagnostic]]:
    """Extract only statically provable entity IDs and report dynamic calls.

    The template is never rendered. Jinja's parser identifies locally bound names;
    its lexer excludes plain text, comments, strings, methods, and block crossings.
    Dynamic arguments are never completed or guessed.
    """
    normalized, original_offsets = _normalize_template(template)
    try:
        parsed_template = _JINJA_ENVIRONMENT.parse(normalized)
    except TemplateSyntaxError as err:
        return [], [
            ParserDiagnostic(
                code="template_syntax_error",
                message=str(err),
                reference="",
                line=err.lineno or 1,
                column=1,
            )
        ]

    bound_names = _bound_names(parsed_template)
    allowed_functions = _SUPPORTED_FUNCTIONS - bound_names
    tokens = _syntax_tokens(normalized)

    references: list[StaticReference] = []
    diagnostics: list[ParserDiagnostic] = []
    for function, start in _global_function_calls(tokens, allowed_functions):
        if function == "expand":
            parsed, call_diagnostics = _parse_expand_call(
                normalized,
                template,
                original_offsets,
                start,
            )
        else:
            parsed, call_diagnostics = _parse_direct_call(
                normalized,
                template,
                original_offsets,
                start,
                function,
            )
        references.extend(parsed)
        diagnostics.extend(call_diagnostics)

    if "states" not in bound_names:
        references.extend(
            _dotted_state_references(
                normalized,
                template,
                original_offsets,
                tokens,
            )
        )

    references.sort(key=lambda item: (item.line, item.column))
    diagnostics.sort(key=lambda item: (item.line, item.column, item.code))
    return references, diagnostics


def _normalize_template(template: str) -> tuple[str, list[int]]:
    """Normalize line endings and map each normalized offset to the original."""
    characters: list[str] = []
    original_offsets: list[int] = []
    original_index = 0
    while original_index < len(template):
        original_offsets.append(original_index)
        char = template[original_index]
        if char == "\r":
            characters.append("\n")
            original_index += (
                2
                if original_index + 1 < len(template)
                and template[original_index + 1] == "\n"
                else 1
            )
        else:
            characters.append(char)
            original_index += 1
    original_offsets.append(len(template))
    return "".join(characters), original_offsets


def _bound_names(template: nodes.Template) -> set[str]:
    """Return names locally defined anywhere in the Jinja template."""
    result = {
        node.name
        for node in template.find_all(nodes.Name)
        if node.ctx in {"store", "param"}
    }
    result.update(node.name for node in template.find_all(nodes.Macro))
    result.update(node.target for node in template.find_all(nodes.Import))
    for node in template.find_all(nodes.FromImport):
        result.update(
            name[1] if isinstance(name, tuple) else name for name in node.names
        )
    return result


def _syntax_tokens(template: str) -> list[_LocatedToken]:
    """Return source-located name/operator tokens grouped by Jinja region."""
    result: list[_LocatedToken] = []
    cursor = 0
    region = 0
    active_region: int | None = None
    for _line, token_type, value in _JINJA_ENVIRONMENT.lex(template):
        start = template.find(value, cursor)
        if start == -1:  # pragma: no cover - defensive lexer compatibility
            break
        cursor = start + len(value)
        if token_type in {"variable_begin", "block_begin"}:
            region += 1
            active_region = region
        elif token_type in {"variable_end", "block_end"}:
            active_region = None
        elif token_type in {"name", "operator"} and active_region is not None:
            result.append((token_type, value, start, active_region))
    return result


def _global_function_calls(
    tokens: list[_LocatedToken], allowed_functions: set[str]
) -> list[tuple[str, int]]:
    """Locate genuine global calls, excluding methods, filters, and tests."""
    calls: list[tuple[str, int]] = []
    for index, (token_type, value, start, region) in enumerate(tokens):
        if token_type != "name" or value not in allowed_functions:
            continue
        if (
            index + 1 >= len(tokens)
            or tokens[index + 1][:2] != ("operator", "(")
            or tokens[index + 1][3] != region
        ):
            continue
        if index > 0 and tokens[index - 1][3] == region:
            previous_type, previous_value = tokens[index - 1][:2]
            if previous_type == "operator" and previous_value in {".", "|"}:
                continue
            if previous_type == "name" and previous_value == "is":
                continue
        calls.append((value, start))
    return calls


def _parse_direct_call(
    normalized: str,
    original: str,
    original_offsets: list[int],
    start: int,
    function: str,
) -> tuple[list[StaticReference], list[ParserDiagnostic]]:
    """Classify the first argument of one direct entity function call."""
    normalized_reference, original_reference = _call_references(
        normalized, original, original_offsets, start
    )
    position = _position(normalized, start)
    call = _isolated_global_call(normalized_reference, function)
    if call is None or not call.args:
        return [], [_dynamic_diagnostic(original_reference, position)]

    first_argument = call.args[0]
    if not isinstance(first_argument, nodes.Const) or not isinstance(
        first_argument.value, str
    ):
        return [], [_dynamic_diagnostic(original_reference, position)]

    entity_id = first_argument.value
    if not re.fullmatch(_ENTITY, entity_id):
        return [], [
            ParserDiagnostic(
                code="invalid_static_entity_id",
                message=(
                    "The first argument is a literal but not a valid static entity ID."
                ),
                reference=original_reference,
                **position,
            )
        ]

    return [
        StaticReference(
            entity_id=entity_id,
            reference=original_reference,
            **position,
        )
    ], []


def _parse_expand_call(
    normalized: str,
    original: str,
    original_offsets: list[int],
    start: int,
) -> tuple[list[StaticReference], list[ParserDiagnostic]]:
    """Parse one isolated expand call without rendering it."""
    normalized_reference, original_reference = _call_references(
        normalized, original, original_offsets, start
    )
    position = _position(normalized, start)
    call = _isolated_global_call(normalized_reference, "expand")
    if call is None:
        return [], [_dynamic_diagnostic(original_reference, position)]

    literal_values: list[str] = []
    has_dynamic = bool(call.kwargs or call.dyn_args or call.dyn_kwargs)
    has_invalid_literal = False
    for argument in call.args:
        values, dynamic, invalid_literal = _collect_expand_literals(argument)
        literal_values.extend(values)
        has_dynamic |= dynamic
        has_invalid_literal |= invalid_literal

    references: list[StaticReference] = []
    for entity_id in literal_values:
        if re.fullmatch(_ENTITY, entity_id):
            references.append(
                StaticReference(
                    entity_id=entity_id,
                    reference=original_reference,
                    **position,
                )
            )
        else:
            has_invalid_literal = True

    diagnostics: list[ParserDiagnostic] = []
    if has_dynamic:
        diagnostics.append(_dynamic_diagnostic(original_reference, position))
    if has_invalid_literal:
        diagnostics.append(
            ParserDiagnostic(
                code="invalid_static_entity_id",
                message="An expand() literal is not a valid static entity ID.",
                reference=original_reference,
                **position,
            )
        )
    return references, diagnostics


def _call_references(
    normalized: str,
    original: str,
    original_offsets: list[int],
    start: int,
) -> tuple[str, str]:
    """Return normalized parse text and the exact original call text."""
    normalized_reference = _call_reference(normalized, start)
    normalized_end = start + len(normalized_reference)
    original_reference = original[
        original_offsets[start] : original_offsets[normalized_end]
    ]
    return normalized_reference, original_reference


def _isolated_global_call(call_reference: str, function: str) -> nodes.Call | None:
    """Parse an isolated call and require the expected global function name."""
    try:
        parsed = _JINJA_ENVIRONMENT.parse(f"{{{{ {call_reference} }}}}")
    except TemplateSyntaxError:
        return None

    if (
        len(parsed.body) != 1
        or not isinstance(parsed.body[0], nodes.Output)
        or len(parsed.body[0].nodes) != 1
        or not isinstance(call := parsed.body[0].nodes[0], nodes.Call)
        or not isinstance(call.node, nodes.Name)
        or call.node.name != function
    ):
        return None
    return call


def _collect_expand_literals(node: nodes.Node) -> tuple[list[str], bool, bool]:
    """Collect static strings and classify unsupported expand argument nodes."""
    if isinstance(node, nodes.Const):
        if isinstance(node.value, str):
            return [node.value], False, False
        return [], False, True

    if isinstance(node, (nodes.List, nodes.Tuple)):
        values: list[str] = []
        has_dynamic = False
        has_invalid_literal = False
        for item in node.items:
            item_values, dynamic, invalid_literal = _collect_expand_literals(item)
            values.extend(item_values)
            has_dynamic |= dynamic
            has_invalid_literal |= invalid_literal
        return values, has_dynamic, has_invalid_literal

    return [], True, False


def _dotted_state_references(
    normalized: str,
    original: str,
    original_offsets: list[int],
    tokens: list[_LocatedToken],
) -> list[StaticReference]:
    """Extract global states.domain.object and optional .state expressions."""
    references: list[StaticReference] = []
    for index, (token_type, value, start, region) in enumerate(tokens):
        if token_type != "name" or value != "states":
            continue
        if (
            index > 0
            and tokens[index - 1][3] == region
            and tokens[index - 1][:2] == ("operator", ".")
        ):
            continue
        if index + 4 >= len(tokens):
            continue
        sequence = tokens[index + 1 : index + 5]
        if any(token[3] != region for token in sequence):
            continue
        if (
            sequence[0][:2] != ("operator", ".")
            or sequence[1][0] != "name"
            or sequence[2][:2] != ("operator", ".")
            or sequence[3][0] != "name"
        ):
            continue

        entity_id = f"{sequence[1][1]}.{sequence[3][1]}"
        if not re.fullmatch(_ENTITY, entity_id):
            continue
        end = sequence[3][2] + len(sequence[3][1])
        if (
            index + 6 < len(tokens)
            and tokens[index + 5][3] == region
            and tokens[index + 6][3] == region
            and tokens[index + 5][:2] == ("operator", ".")
            and tokens[index + 6][:2] == ("name", "state")
        ):
            end = tokens[index + 6][2] + len(tokens[index + 6][1])
        references.append(
            StaticReference(
                entity_id=entity_id,
                reference=original[original_offsets[start] : original_offsets[end]],
                **_position(normalized, start),
            )
        )
    return references


def _dynamic_diagnostic(reference: str, position: dict[str, int]) -> ParserDiagnostic:
    """Build the standard conservative dynamic-reference diagnostic."""
    return ParserDiagnostic(
        code="dynamic_entity_reference",
        message="Dynamic entity reference ignored; no entity ID was guessed.",
        reference=reference,
        **position,
    )


def _position(text: str, offset: int) -> dict[str, int]:
    """Return one-based line and column for an offset."""
    line = text.count("\n", 0, offset) + 1
    last_newline = text.rfind("\n", 0, offset)
    column = offset + 1 if last_newline == -1 else offset - last_newline
    return {"line": line, "column": column}


def _call_reference(text: str, start: int) -> str:
    """Return the concrete call text without evaluating nested expressions."""
    depth = 0
    quote: str | None = None
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
        elif char == "\n" and depth <= 0:
            break
    return text[start:].splitlines()[0].strip()
