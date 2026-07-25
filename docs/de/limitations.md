# Bekannte Grenzen

## Nur UI-basierte Template-Helfer

Templates aus `configuration.yaml`, `templates.yaml`, Packages oder anderen YAML-Dateien werden **nicht** gescannt. Home Assistant bietet keine stabile öffentliche API, um alle ursprünglichen YAML-Template-Quellen aufzuzählen.

## Kein Rendern

Jinja wird **nicht** gerendert oder semantisch ausgeführt. Die konservative statische Extraktion erkennt nur direkte, statische Referenzen. Indirekte Referenzen werden bewusst nicht erkannt.

## Dynamische Referenzen

Dynamisch konstruierte Entity-IDs können nicht aufgelöst werden:

```jinja2
{{ states('sensor.' ~ variable) }}           ← nicht auflösbar
{{ state_attr(entity_variable, 'attribute') }} ← nicht auflösbar
```

Sie erzeugen Parser-Diagnostik, aber nie eine erfundene fehlende Entity.

## Internes Schema

Die öffentliche Config-Entry-API wird nur lesend genutzt. Das interne Options-Feld-Schema der `template`-Integration kann sich mit HA-Releases ändern. Zugriff ist in `template_sources.py` isoliert und getestet. Unbekannte neuere Schema-Versionen werden als Lade-Fehler gemeldet, nicht geraten.

## Kein Scan anderer Bereiche

Templates in Automatisierungen, Scripts, Szenen, Dashboards, Blueprints und anderen Integrationen werden **nicht** gescannt.

## Keine Reparatur

Die Integration meldet Probleme, repariert aber keine Referenzen und bietet keine automatischen Reparaturen an.

## Attribut-Größenlimit

Sehr große Ergebnisse können das State-Attribut-Größenlimit von Home Assistant erreichen. Export- und Reparatur-Funktionen sind zukünftige Arbeit.

## Was NICHT als fehlend gilt

- Entities mit Status `unavailable` — solange Registry-Eintrag existiert
- Entities mit Status `unknown` — solange Registry-Eintrag existiert
- Entities mit Status `disabled` — solange Registry-Eintrag existiert
- Entities ohne aktuellen State — solange Registry-Eintrag existiert