# Anforderungen

## Laufzeit

| Anforderung | Version/Stand |
|---|---|
| Home Assistant | 2026.7.3 oder neuer |
| HACS | aktuelle Version für HACS-Installation |
| YAML-Konfiguration | nicht erforderlich und nicht unterstützt |

## Teststände und Installationswege

Die Mindestversion oben bleibt erhalten und ist nicht der neueste Teststand.
Reguläre Tests verwenden HA **2026.10.4** und pytest-homeassistant-custom-component
**0.13.375**. Die Typprüfung läuft isoliert mit kompatiblen **2026.9.2**-Stubs
und deren erforderlichem September-Core. Die neuesten **2026.10.0**-Stubs erzeugen
Coordinator-/Probatio-Typvertragsfehler im unveränderten Code. Dieser erhaltene
Pin ist nicht die Runtime-Baseline und wird nie mit dem Oktober-Testextra installiert.
November **2026.11.0b0/b1** werden separat mit einem echten Core-Harness
geprüft, nicht mit dem inkompatiblen Oktober-Pytest-Plugin. Beide bleiben Beta.

Die drei neuen Helfertypen, exakten Feldpfade, Ignore-Matches, Notification
create/update/dismiss und Optionsreload des Kandidaten bestanden eine gezielte
Live-Abnahme unter b0. Browserdarstellung und Recorder-Persistenz sind nicht
zertifiziert. Der lokale Harness startet keinen vollständigen HTTP-/Frontend-/Recorder-Stack.

HACS und der integrierte Marketplace der November-Beta sind unterschiedliche
Installationswege. Die Kandidateninstallation über Marketplace wurde nur unter
b0 geprüft; dessen Community-Erweiterungs-Risikoerklärung selbst lesen und
bestätigen. Das ist weder eine pauschale Marketplace-Zertifizierung noch eine
Aufforderung, von HACS zu wechseln.

## Integration

| Eigenschaft | Wert |
|---|---|
| Integration Type | `service` |
| IoT Class | `local_polling` |
| Config Flow | ja |
| Config Entries | genau einer |
| Abhängigkeiten | `persistent_notification`, `template` |
| Plattform | `sensor` |
| erwartete Entity | `sensor.template_entity_checker` |

## Sprachen

Englische und deutsche Oberflächentexte sind enthalten.

## Veröffentlichungsstand

| Version | Stand |
|---|---|
| `0.1.5` | Stand dieser Dokumentation |
| `0.1.4` | vorherige stabile Version |
