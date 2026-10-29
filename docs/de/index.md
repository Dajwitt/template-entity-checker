# Template Entity Checker

**Dokumentationsstand: Version 0.1.5** · Home Assistant Custom Integration

Template Entity Checker prüft über die Benutzeroberfläche erstellte Template-Helfer auf statische Entity-Referenzen, die nicht mehr existieren.

Die Integration liest Template-Helfer über die öffentliche Config-Entry-API. Sie rendert oder verändert **keine** Templates, repariert keine Referenzen, rät keine dynamischen Entity-IDs und liest oder schreibt keine `.storage`-Dateien.

## Scope

**Nur UI-basierte Template-Helfer.** Templates aus `configuration.yaml`, `templates.yaml`, Packages oder anderen YAML-Dateien werden nicht gescannt.

## Neu in 0.1.5

- 20 bestätigte UI-Template-Helfertypen, neu `climate`, `media_player` und `water_heater`, einschließlich `additional_options.away_mode`
- Kompatibilität gegen HA `2026.11.0b0` und `2026.11.0b1` geprüft; Home Assistant November bleibt Beta, dieser Integrationsrelease ist regulär
- Schema `2.1`, UI-only-Grenze und Ausschluss von Aktionen bleiben unverändert; siehe [Teststände und Grenzen](./requirements.md)

## Neu in 0.1.4

- Unterstützung für das Template-Helfer-Config-Entry-Schema `2.1` aus Home Assistant 2026.8
- umfangreiche Live-Funddetails werden nicht mehr in der Recorder-Historie gespeichert; kompakte Scan-Verlaufsdaten bleiben erhalten

## Neu in 0.1.3

- durchsuchbare Auswahl für das optionale Helfer-Label; freie Eingaben sind gesperrt, eine zuvor gespeicherte gelöschte Label-ID bleibt zum Entfernen sichtbar und gespeichert werden kann höchstens ein Label

## Neu in 0.1.2

- `has_value` als Funktion, Filter und Jinja-Test
- suchbare Mehrfachauswahl für exakt ignorierte Entity-IDs; fehlende IDs bleiben frei eingebbar
- optionaler Ausschluss kompletter Template-Helfer über ein frei gewähltes Home-Assistant-Label
- transparente Angaben zu wirksamem Label, ignorierten Helfern und ignorierten Funden
- nativer Ein/Aus-Schalter für persistente Benachrichtigungen

## Schnellstart

1. [Installation](./installation.md) über HACS
2. [Konfiguration](./configuration.md) über **Einstellungen → Geräte & Dienste**
3. [Ergebnisse prüfen](./sensor.md) über `sensor.template_entity_checker`

## Dokumentation

| Bereich | Inhalt |
|---|---|
| [Installation](./installation.md) | HACS- und manuelle Installation |
| [Konfiguration](./configuration.md) | Config Flow, Options Flow, Einstellungen |
| [Funktionsweise](./how-it-works.md) | Scan-Prozess und Template-Helfer-Typen |
| [Unterstützte Syntax](./supported-syntax.md) | Statische Jinja-Referenzen mit Beispielen |
| [Result-Sensor](./sensor.md) | Zustand und Attribute |
| [Aktion](./services.md) | `template_entity_checker.scan_now` |
| [Events](./events.md) | `template_entity_checker_result_changed` |
| [Benachrichtigungen](./notifications.md) | Persistente Benachrichtigung |
| [Ausschlüsse](./ignore-list.md) | Exakte IDs und Helfer-Label |
| [Diagnostik](./diagnostics.md) | Diagnostics-Download und Inhalt |
| [Bekannte Grenzen](./limitations.md) | Was nicht aufgelöst werden kann |
| [Fehlerbehebung](./troubleshooting.md) | Probleme eingrenzen |
| [Anforderungen](./requirements.md) | Versionen und Plattformen |
