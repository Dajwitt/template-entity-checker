# Repository rules

- Never modify UI or YAML templates.
- Never read or write Home Assistant `.storage` directly.
- Never guess dynamic entity IDs.
- Missing means absent from both state machine and entity registry.
- Keep missing references, parser diagnostics, and source load errors separate.
- Verify version-dependent behavior against official docs or Home Assistant Core.

Quality gate:

```bash
uv run ruff check custom_components tests
uv run mypy custom_components/template_entity_checker
uv run pytest -q --cov=custom_components/template_entity_checker --cov-report=term-missing --cov-fail-under=90
python3 scripts/check_legacy_references.py
```
