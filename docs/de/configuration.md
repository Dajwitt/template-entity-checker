# Konfiguration

Konfiguration und spätere Änderungen erfolgen über Home Assistants Config Flow und Options Flow. Eine YAML-Konfiguration ist nicht erforderlich.

> Diese Seite beschreibt die unveröffentlichte Preview `0.1.3b1`. Die öffentliche stabile Version `0.1.2` besitzt noch keine durchsuchbare Labelauswahl.

## Ersteinrichtung

Nach Installation und Neustart:

1. Öffne **Einstellungen → Geräte & Dienste**.
2. Wähle **Integration hinzufügen**.
3. Suche nach **Template Entity Checker**.
4. Setze das Scan-Intervall in Minuten (Standard: 15).
5. Aktiviere oder deaktiviere persistente Benachrichtigungen.
6. Wähle optional exakt zu ignorierende Entity-IDs aus oder gib fehlende IDs frei ein.
7. Suche und wähle optional ein Home-Assistant-Label für komplett zu ignorierende Template-Helfer.

## Konfigurationsfelder

| Feld | Typ | Standard | Beschreibung |
|---|---|---|---|
| Scan-Intervall | Ganzzahl (1–1440) | 15 Minuten | Zeit zwischen automatischen Scans |
| Benachrichtigungen | Ein/Aus | An | Persistente Benachrichtigung bei aktiven Funden |
| Exakt ignorierte Entity-IDs | suchbare Mehrfachauswahl mit freier Eingabe | leer | Unterdrückt die gewählten fehlenden Ziel-IDs vollständig |
| Label für ignorierte Template-Helfer | durchsuchbare Auswahl ohne freie Eingabe, maximal eines | leer | Unterdrückt Funde aus Helfern, deren erzeugte Entity dieses Label direkt trägt |

## Suchbare Entity-Auswahl

Im Options Flow enthält die Auswahlliste:

- aktuell gemeldete fehlende Entity-IDs,
- bereits ignorierte Funde,
- schon gespeicherte Ignore-IDs.

Da eine fehlende Entity nicht mehr in Home Assistants Entity Registry stehen muss, sind weiterhin eigene syntaktisch gültige Entity-IDs eingebbar.

## Helfer über ein Label ausschließen

Das optionale Label wird aus Home Assistants aktueller Label-Registry gewählt und intern über seine stabile Label-ID gespeichert.

- Die Auswahl ist durchsuchbar und erlaubt keine freie Eingabe. Sie bietet aktuelle Labels sowie gegebenenfalls die zuvor gespeicherte ID eines gelöschten Labels an, damit sie entfernt werden kann.
- Es kann höchstens ein Label gespeichert werden.
- Das Label muss direkt an der vom Template-Helfer erzeugten Entity gesetzt sein.
- Labels von Geräten oder Bereichen werden nicht vererbt.
- Eine Umbenennung des Labels bleibt wirksam.
- Wird das gespeicherte Label gelöscht, werden keine Helfer mehr darüber ausgeschlossen; der Scan bleibt vollständig und meldet das Label als nicht verfügbar.
- Exakte Entity-IDs und Label-Ausschluss können parallel verwendet werden.

## Options Flow

Alle Felder können später über **Einstellungen → Geräte & Dienste → Template Entity Checker → Konfigurieren** geändert werden. Nach dem Speichern wird die Integration neu geladen und scannt mit den neuen Einstellungen.

## Single Instance und Migration

Es wird nur eine Instanz unterstützt. Ein zweiter Setup-Versuch wird abgebrochen.

Bestehende Config Entries der alten Flow-Version 1 werden automatisch auf Version 2 migriert. Die frühere Auswahl einzelner Template-Helfer-Typen wird aus Daten und Optionen entfernt; seitdem werden alle bestätigten Typen automatisch geprüft. Alte textbasierte Ignore-Werte bleiben lesbar und werden beim nächsten Speichern in die neue Liste überführt.

## Bewusste Grenzen

- keine Wildcards wie `sensor.wohnraum_*`
- keine Auswahl einzelner Template-Helfer-Typen
- keine Dashboard-Auswahl
- keine YAML-Konfiguration
