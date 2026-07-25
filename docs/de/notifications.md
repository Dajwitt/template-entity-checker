# Benachrichtigungen

Wenn Benachrichtigungen aktiviert sind, verwaltet die Integration eine einzelne persistente Notification.

## Verhalten

- **Eine** feste Notification-ID — keine Duplikate bei wiederholten Scans
- Nur bei **verändertem** komplettem Ergebnis wird die Notification aktualisiert
- Identische Ergebnisse erzeugen keine neue Notification
- Ergebnisse werden nach Template-Helfer gruppiert
- Ein sauberer Scan (0 fehlende) entfernt die Notification
- Deaktivieren von Benachrichtigungen entfernt die Notification ebenfalls
- Ausschließlich ignorierte Funde erzeugen keine Notification

## Partielles Fehlschlagen

Bei einem Teil-Fehler (ein Template-Helfer nicht ladbar) wird die bestehende Notification **nicht** verändert — unvollständige Eingaben dürfen kein echtes Problem verstecken.

## Beispiel: Notification-Text (Deutsch)

```
Template Entity Checker: 2 fehlende Entities

**Template-Helfer**

Durchschnitt Luftfeuchte
• sensor.wohnraum_doku_altwert
• sensor.keller_doku_altwert

Vollständige Liste: Sensorattribut `missing_entities`
```

## Sprache

Titel und Text folgen der HA-Spracheinstellung (Deutsch oder Englisch).