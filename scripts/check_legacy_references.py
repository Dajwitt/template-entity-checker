"""Fail on accidental references to the separate predecessor project."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = (
    "dashboard_entity_checker",
    "Dashboard Entity Checker",
    "dashboard-entity-checker",
)
ALLOWED = {
    Path("documentation/phase-1-analyse.md"),
    Path("documentation/architekturentscheidungen.md"),
    Path("documentation/qualitaetsbericht.md"),
    Path("documentation/repository-und-implementierung.md"),
    Path("scripts/check_legacy_references.py"),
}
SKIP_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache"}

violations: list[str] = []
for path in ROOT.rglob("*"):
    if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
        continue
    relative = path.relative_to(ROOT)
    if relative in ALLOWED:
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    for value in FORBIDDEN:
        if value in text:
            violations.append(f"{relative}: {value}")

if violations:
    print("Accidental predecessor references found:")
    print("\n".join(violations))
    sys.exit(1)
print("No accidental predecessor project references found.")
