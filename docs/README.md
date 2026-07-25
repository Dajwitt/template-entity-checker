# Documentation maintenance

The documentation is bilingual and keeps Markdown as the single source of truth.

## Structure

- `en/` — English source pages
- `de/` — German source pages
- `build_html.py` — standard-library generator
- `site/index.html` — generated self-contained GitHub Pages site

## Update workflow

1. Update the matching page in both `en/` and `de/`.
2. Run:

   ```bash
   python3 docs/build_html.py
   ```

3. Review `docs/site/index.html` locally.
4. Commit both Markdown changes and the generated site.

The Documentation workflow regenerates the site and fails when the committed HTML is stale. Pushes to `main` deploy `docs/site/` through GitHub Pages.

## GitHub Pages configuration

This repository is configured to publish through **GitHub Actions**. For a new repository or fork, an administrator must first open **Settings → Pages → Build and deployment** and set **Source** to **GitHub Actions**. The normal workflow token does not perform this one-time enablement automatically.

Public project URL:

```text
https://dajwitt.github.io/template-entity-checker/
```
