# Installation

Template Entity Checker is installed as a Home Assistant custom integration. This documentation describes the unreleased `0.1.3b1` preview; the current public stable version is `0.1.2` and does not include the searchable label selection yet.

## Requirements

- Home Assistant 2026.7.3 or newer
- a current HACS version

## Install through HACS

1. Open **HACS** in Home Assistant.
2. Open the three-dot menu in the top-right corner.
3. Select **Custom repositories**.
4. Enter:

   ```text
   https://github.com/Dajwitt/template-entity-checker
   ```

5. Select the **Integration** category and add the repository.
6. Open **Template Entity Checker** in HACS and select **Download**.
7. Restart Home Assistant.
8. Continue with [Configuration](./configuration.md).

Do not add anything to `configuration.yaml`.

## Manual installation

1. For a stable installation, download the latest release from GitHub. Preview `0.1.3b1` has not been published as a release yet.
2. Copy `custom_components/template_entity_checker` to:

   ```text
   /config/custom_components/template_entity_checker
   ```

3. Restart Home Assistant.
4. Continue with [Configuration](./configuration.md).
