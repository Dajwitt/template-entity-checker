"""Conservative static parser for Home Assistant Jinja entity references."""

from __future__ import annotations

import re

from .models import ParserDiagnostic, StaticReference

_ENTITY = r"[a-z_][a-z0-9_]*\.[a-z0-9_]+"
_FUNCTIONS = ("states", "state_attr", "is_state", "is_state_attr", "expand")
_FUNCTION_NAMES = "|".join(_FUNCTIONS)

_STATIC_CALL_RE = re.compile(
    rf"\b(?P<function>{_FUNCTION_NAMES})\s*\(\s*"
    rf"(?P<quote>['\"])(?P<entity>{_ENTITY})(?P=quote)"
)
_FUNCTION_START_RE = re.compile(rf"\b(?P<function>{_FUNCTION_NAMES})\s*\(")
_LITERAL_FIRST_ARGUMENT_RE = re.compile(
    r"\s*(?P<quote>['\"])(?P<literal>.*?)(?P=quote)\s*(?=[,)])"
)
_DOT_STATE_RE = re.compile(rf"\bstates\.(?P<entity>{_ENTITY})(?:\.state)?(?![a-z0-9_])")


def parse_template(
    template: str,
) -> tuple[list[StaticReference], list[ParserDiagnostic]]:
    """Extract only statically provable entity IDs and report dynamic calls.

    The template is never rendered. Dynamic arguments are never completed or guessed.
    """
    references: list[StaticReference] = []
    diagnostics: list[ParserDiagnostic] = []
    static_call_starts: set[int] = set()

    for match in _STATIC_CALL_RE.finditer(template):
        static_call_starts.add(match.start())
        references.append(
            StaticReference(
                entity_id=match.group("entity"),
                reference=_call_reference(template, match.start()),
                **_position(template, match.start()),
            )
        )

    for match in _DOT_STATE_RE.finditer(template):
        references.append(
            StaticReference(
                entity_id=match.group("entity"),
                reference=match.group(0),
                **_position(template, match.start()),
            )
        )

    for match in _FUNCTION_START_RE.finditer(template):
        if match.start() in static_call_starts:
            continue
        argument_start = match.end()
        remainder = template[argument_start:]
        if _LITERAL_FIRST_ARGUMENT_RE.match(remainder):
            code = "invalid_static_entity_id"
            message = (
                "The first argument is a literal but not a valid static entity ID."
            )
        else:
            code = "dynamic_entity_reference"
            message = "Dynamic entity reference ignored; no entity ID was guessed."
        diagnostics.append(
            ParserDiagnostic(
                code=code,
                message=message,
                reference=_call_reference(template, match.start()),
                **_position(template, match.start()),
            )
        )

    references.sort(key=lambda item: (item.line, item.column, item.entity_id))
    diagnostics.sort(key=lambda item: (item.line, item.column, item.code))
    return references, diagnostics


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
