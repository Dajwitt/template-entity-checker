# Documentation maintenance

The documentation is bilingual and keeps Markdown as the single source of truth.

## Structure

- `en/` — English source pages
- `de/` — German source pages
- `build_html.py` — standard-library generator
- `site/index.html` — generated self-contained GitHub Pages site

## Update workflow

1. Review the documentation impact for every user-facing change. This includes configuration fields, supported syntax, sensor attributes, actions, events, notifications, diagnostics, installation requirements, and known limits.
2. Update the matching page in both `en/` and `de/` in the same branch as the code change. During ordinary feature development, describe unreleased behavior as **Unreleased / In preparation**. A final release candidate may name its target documentation version, but it must not claim that the version is already publicly released or available through HACS before the tag exists. Prefer durable wording that remains true before and after publication.
3. Run:

   ```bash
   python3 docs/build_html.py
   ```

4. Review `docs/site/index.html` locally in both languages, including navigation, search, theme switching, and the mobile menu.
5. Commit both Markdown changes and the generated site. Never edit `docs/site/index.html` by hand.

The Documentation workflow regenerates the site and fails when the committed HTML is stale. Pushes to `main` deploy `docs/site/` through GitHub Pages. Release-version statements in both languages must stay synchronized with the integration version metadata and must distinguish the documented target version from verified public availability.

## GitHub Pages configuration

This repository is configured to publish through **GitHub Actions**. For a new repository or fork, an administrator must first open **Settings → Pages → Build and deployment** and set **Source** to **GitHub Actions**. The normal workflow token does not perform this one-time enablement automatically.

Public project URL:

```text
https://dajwitt.github.io/template-entity-checker/
```
