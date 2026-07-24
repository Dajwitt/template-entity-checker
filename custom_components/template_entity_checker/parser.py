"""Conservative static parser for Home Assistant Jinja entity references."""

from __future__ import annotations

import re
from collections import defaultdict, deque
from collections.abc import Iterable

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
_CallPermissions = dict[tuple[str, int], deque[bool]]
_DottedPermissions = dict[int, deque[bool]]


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

    call_permissions, dotted_permissions = _reference_permissions(parsed_template)
    tokens = _syntax_tokens(normalized)

    references: list[StaticReference] = []
    diagnostics: list[ParserDiagnostic] = []
    for function, start in _global_function_calls(
        normalized,
        tokens,
        call_permissions,
    ):
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

    references.extend(
        _dotted_state_references(
            normalized,
            template,
            original_offsets,
            tokens,
            dotted_permissions,
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


def _reference_permissions(
    template: nodes.Template,
) -> tuple[_CallPermissions, _DottedPermissions]:
    """Map source-ordered expressions to decisions from their lexical scope."""
    call_permissions: defaultdict[tuple[str, int], deque[bool]] = defaultdict(deque)
    dotted_permissions: defaultdict[int, deque[bool]] = defaultdict(deque)
    seen_dotted_bases: set[int] = set()
    _walk_reference_nodes(
        template,
        frozenset(),
        call_permissions,
        dotted_permissions,
        seen_dotted_bases,
    )
    return dict(call_permissions), dict(dotted_permissions)


def _walk_reference_nodes(
    node: nodes.Node,
    bound_names: frozenset[str],
    call_permissions: defaultdict[tuple[str, int], deque[bool]],
    dotted_permissions: defaultdict[int, deque[bool]],
    seen_dotted_bases: set[int],
) -> None:
    """Walk the Jinja AST while respecting lexical binding scopes."""
    if isinstance(node, nodes.Template):
        _walk_body(
            node.body,
            bound_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )
        return

    if isinstance(node, nodes.For):
        _walk_reference_nodes(
            node.iter,
            bound_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )
        loop_names = bound_names | _target_names(node.target)
        if node.test is not None:
            _walk_reference_nodes(
                node.test,
                loop_names,
                call_permissions,
                dotted_permissions,
                seen_dotted_bases,
            )
        _walk_body(
            node.body,
            loop_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )
        _walk_body(
            node.else_,
            bound_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )
        return

    if isinstance(node, nodes.Macro):
        _walk_children(
            node.defaults,
            bound_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )
        macro_names = (
            bound_names | {node.name} | {argument.name for argument in node.args}
        )
        _walk_body(
            node.body,
            macro_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )
        return

    if isinstance(node, nodes.With):
        _walk_children(
            node.values,
            bound_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )
        target_names = frozenset().union(
            *(_target_names(target) for target in node.targets)
        )
        with_names = bound_names | target_names
        _walk_body(
            node.body,
            with_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )
        return

    if isinstance(node, nodes.CallBlock):
        _walk_children(
            node.defaults,
            bound_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )
        _walk_reference_nodes(
            node.call,
            bound_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )
        call_names = bound_names | {argument.name for argument in node.args}
        _walk_body(
            node.body,
            call_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )
        return

    if isinstance(node, nodes.AssignBlock):
        if node.filter is not None:
            filter_names = bound_names | _scope_bindings(node.body)
            _walk_reference_nodes(
                node.filter,
                filter_names,
                call_permissions,
                dotted_permissions,
                seen_dotted_bases,
            )
        _walk_body(
            node.body,
            bound_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )
        return

    if isinstance(node, nodes.FilterBlock):
        filter_names = bound_names | _scope_bindings(node.body)
        _walk_reference_nodes(
            node.filter,
            filter_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )
        _walk_body(
            node.body,
            bound_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )
        return

    if isinstance(node, nodes.OverlayScope):
        _walk_reference_nodes(
            node.context,
            bound_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )
        _walk_body(
            node.body,
            bound_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )
        return

    if isinstance(node, (nodes.Block, nodes.Scope)):
        _walk_body(
            node.body,
            bound_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )
        return

    if isinstance(node, nodes.If):
        _walk_reference_nodes(
            node.test,
            bound_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )
        _walk_body(
            node.body,
            bound_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )
        _walk_children(
            node.elif_,
            bound_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )
        _walk_body(
            node.else_,
            bound_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )
        return

    if (
        isinstance(node, nodes.Call)
        and isinstance(node.node, nodes.Name)
        and node.node.name in _SUPPORTED_FUNCTIONS
    ):
        call_permissions[(node.node.name, node.lineno)].append(
            node.node.name not in bound_names
        )

    if isinstance(node, nodes.Getattr):
        base = _dotted_states_base(node)
        if base is not None and id(base) not in seen_dotted_bases:
            seen_dotted_bases.add(id(base))
            dotted_permissions[base.lineno].append("states" not in bound_names)

    _walk_children(
        node.iter_child_nodes(),
        bound_names,
        call_permissions,
        dotted_permissions,
        seen_dotted_bases,
    )


def _walk_children(
    children: Iterable[nodes.Node],
    bound_names: frozenset[str],
    call_permissions: defaultdict[tuple[str, int], deque[bool]],
    dotted_permissions: defaultdict[int, deque[bool]],
    seen_dotted_bases: set[int],
) -> None:
    """Walk child nodes with one shared lexical scope."""
    for child in children:
        _walk_reference_nodes(
            child,
            bound_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )


def _walk_body(
    body: Iterable[nodes.Node],
    bound_names: frozenset[str],
    call_permissions: defaultdict[tuple[str, int], deque[bool]],
    dotted_permissions: defaultdict[int, deque[bool]],
    seen_dotted_bases: set[int],
) -> None:
    """Walk statements in execution order and activate same-scope bindings."""
    active_names = bound_names
    for child in body:
        _walk_reference_nodes(
            child,
            active_names,
            call_permissions,
            dotted_permissions,
            seen_dotted_bases,
        )
        active_names |= _scope_bindings((child,))


def _scope_bindings(body: Iterable[nodes.Node]) -> frozenset[str]:
    """Collect bindings in one lexical scope, excluding nested child scopes."""
    result: set[str] = set()

    def collect(node: nodes.Node) -> None:
        if isinstance(node, (nodes.Assign, nodes.AssignBlock)):
            result.update(_target_names(node.target))
            return
        if isinstance(node, nodes.Macro):
            result.add(node.name)
            return
        if isinstance(node, nodes.Import):
            result.add(node.target)
            return
        if isinstance(node, nodes.FromImport):
            result.update(
                name[1] if isinstance(name, tuple) else name for name in node.names
            )
            return
        if isinstance(
            node,
            (
                nodes.For,
                nodes.With,
                nodes.CallBlock,
                nodes.FilterBlock,
                nodes.OverlayScope,
                nodes.Block,
                nodes.Scope,
            ),
        ):
            return
        for child in node.iter_child_nodes():
            collect(child)

    for item in body:
        collect(item)
    return frozenset(result)


def _target_names(target: nodes.Node) -> frozenset[str]:
    """Return names introduced by one assignment-style target."""
    if isinstance(target, nodes.Name):
        return frozenset({target.name})
    if isinstance(target, (nodes.Tuple, nodes.List)):
        return frozenset().union(*(_target_names(item) for item in target.items))
    return frozenset()


def _dotted_states_base(node: nodes.Getattr) -> nodes.Name | None:
    """Return the states base for a valid dotted entity expression."""
    attributes: list[str] = []
    current: nodes.Node = node
    while isinstance(current, nodes.Getattr):
        attributes.append(current.attr)
        current = current.node
    attributes.reverse()
    if not isinstance(current, nodes.Name) or current.name != "states":
        return None
    if len(attributes) == 2 or (len(attributes) == 3 and attributes[-1] == "state"):
        return current
    return None


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
    template: str,
    tokens: list[_LocatedToken],
    permissions: _CallPermissions,
) -> list[tuple[str, int]]:
    """Locate genuine global calls, excluding methods, filters, and tests."""
    calls: list[tuple[str, int]] = []
    for index, (token_type, value, start, region) in enumerate(tokens):
        if token_type != "name" or value not in _SUPPORTED_FUNCTIONS:
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
        if _is_test_name(tokens, index, region):
            continue
        if _is_syntax_name(tokens, index, region):
            continue
        line = _position(template, start)["line"]
        decisions = permissions.get((value, line))
        if decisions is None or not decisions or not decisions.popleft():
            continue
        calls.append((value, start))
    return calls


def _is_test_name(tokens: list[_LocatedToken], index: int, region: int) -> bool:
    """Return whether a name identifies a Jinja `is [not]` test."""
    if index > 0 and tokens[index - 1][3] == region:
        if tokens[index - 1][:2] == ("name", "is"):
            return True
        if (
            tokens[index - 1][:2] == ("name", "not")
            and index > 1
            and tokens[index - 2][3] == region
            and tokens[index - 2][:2] == ("name", "is")
        ):
            return True
    return False


def _is_syntax_name(tokens: list[_LocatedToken], index: int, region: int) -> bool:
    """Return whether a name declares a macro or identifies a filter block."""
    return (
        index > 0
        and tokens[index - 1][3] == region
        and tokens[index - 1][:2] in {("name", "macro"), ("name", "filter")}
    )


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
    permissions: _DottedPermissions,
) -> list[StaticReference]:
    """Extract global states.domain.object and optional .state expressions."""
    references: list[StaticReference] = []
    for index, (token_type, value, start, region) in enumerate(tokens):
        if token_type != "name" or value != "states":
            continue
        if index > 0 and tokens[index - 1][3] == region:
            previous_type, previous_value = tokens[index - 1][:2]
            if previous_type == "operator" and previous_value in {".", "|"}:
                continue
        if _is_test_name(tokens, index, region):
            continue
        if _is_syntax_name(tokens, index, region):
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
        line = _position(normalized, start)["line"]
        decisions = permissions.get(line)
        if decisions is None or not decisions or not decisions.popleft():
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
