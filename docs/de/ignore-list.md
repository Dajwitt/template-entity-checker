# Ausschlüsse

Template Entity Checker bietet zwei getrennte, kombinierbare Ausschlüsse. Beide bleiben im Sensor und in der Diagnostik transparent.

## Exakte fehlende Entity-ID ignorieren

Nutze **Exakt zu ignorierende Entity-IDs**, wenn eine bestimmte Ziel-ID bewusst fehlen darf.

```text
sensor.gartenhaus_beispiel_altwert
binary_sensor.werkstatt_beispiel_altkontakt
```

Die Auswahl ist durchsuchbar und kann mehrere Werte enthalten. Aktuelle Funde und bisherige Werte werden angeboten. Weil wirklich fehlende IDs oft nicht mehr in Home Assistant auswählbar sind, kannst du eine syntaktisch gültige Entity-ID auch frei eingeben.

### Regeln

- nur vollständige Entity-IDs
- keine Wildcards
- Duplikate werden entfernt
- die Existenz wird beim Speichern nicht verlangt

## Template-Helfer über Label ignorieren

Nutze **Label für ignorierte Template-Helfer**, wenn alle Funde aus bestimmten Helfern ausgeblendet werden sollen.

1. Lege in Home Assistant ein frei benanntes Label an oder nutze ein vorhandenes.
2. Weise es direkt der Entity zu, die der Template-Helfer erzeugt.
3. Suche und wähle dieses Label in den Optionen des Template Entity Checkers.

Das Label filtert die **Quelle**, nicht die fehlende Ziel-Entity. Geräte- und Bereichslabels werden nicht vererbt.

Die Auswahl ist durchsuchbar, bietet nur vorhandene Home-Assistant-Labels an und erlaubt höchstens ein Label.

### Fundweise Trennung

Referenzieren ein gelabelter und ein ungelabelter Helfer dieselbe fehlende ID, bleibt der Fund des ungelabelten Helfers aktiv. Nur der Fund aus dem gelabelten Helfer wandert nach `ignored_matches`.

## Transparenz

| Attribut | Inhalt |
|---|---|
| `missing_entities` | aktive, nicht ignorierte Funde |
| `ignored_entities` | konfigurierte exakte Ignore-IDs |
| `ignored_helper_label` | Label-ID, aktueller Name und Verfügbarkeit |
| `ignored_helper_sources` | tatsächlich über das Label ausgeschlossene Helfer |
| `ignored_matches` | durch exakte ID oder Helfer-Label unterdrückte Funde |

### Beispiel

| Entity | Quelle | Regel | Ergebnis |
|---|---|---|---|
| `sensor.gartenhaus_beispiel_altwert` | beliebiger Helfer | exakte ID | `ignored_matches` |
| `binary_sensor.werkstatt_beispiel_altkontakt` | gelabelter Helfer | Helfer-Label | `ignored_matches` |
| `binary_sensor.werkstatt_beispiel_altkontakt` | ungelabelter Helfer | keine | `missing_entities` |
