# Installation

Template Entity Checker wird als Custom-Integration für Home Assistant installiert. Die aktuelle öffentliche stabile Version ist `0.1.2`.

## Voraussetzungen

- Home Assistant 2026.7.3 oder neuer
- HACS 2.0.0 oder neuer

## HACS-Installation

1. Öffne **HACS** in Home Assistant.
2. Öffne das Dreipunkt-Menü oben rechts.
3. Wähle **Custom repositories**.
4. Gib diese Repository-URL ein:

   ```text
   https://github.com/Dajwitt/template-entity-checker
   ```

5. Wähle die Kategorie **Integration** und füge das Repository hinzu.
6. Öffne **Template Entity Checker** in HACS und wähle **Download**.
7. Starte Home Assistant neu.
8. Fahre mit [Konfiguration](./configuration.md) fort.

Füge nichts zu `configuration.yaml` hinzu.

## Manuelle Installation

1. Lade das neueste Release von GitHub herunter.
2. Kopiere `custom_components/template_entity_checker` nach:

   ```text
   /config/custom_components/template_entity_checker
   ```

3. Starte Home Assistant neu.
4. Fahre mit [Konfiguration](./configuration.md) fort.