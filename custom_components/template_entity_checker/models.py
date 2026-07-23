"""Typed result models for Template Entity Checker."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class TemplateSource:
    """One template string read from a UI Template Helper config entry."""

    source_id: str
    helper: str
    template_type: str
    template_field: str
    template: str
    source_type: str = "template_helper"


@dataclass(frozen=True, slots=True)
class StaticReference:
    """One statically resolvable entity reference."""

    entity_id: str
    reference: str
    line: int
    column: int


@dataclass(frozen=True, slots=True)
class ParserDiagnostic:
    """One non-fatal parser diagnostic."""

    code: str
    message: str
    reference: str
    line: int
    column: int


@dataclass(frozen=True, slots=True)
class SourceLoadError:
    """One Template Helper source that could not be safely loaded."""

    source_id: str
    helper: str
    error: str

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return {
            "source_id": self.source_id,
            "helper": self.helper,
            "error": self.error,
        }
