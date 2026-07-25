# Fehlerbehebung

## Sensor zeigt `waiting`

Der erste Scan startet erst, wenn Home Assistant vollständig läuft. Kurz nach einem Neustart ist `waiting` normal. Warte kurz oder rufe `template_entity_checker.scan_now` auf.

## `load_errors` enthält Einträge

Mindestens eine Template-Quelle konnte nicht sicher geladen werden.

1. Prüfe `load_errors` und `last_error` im Sensor.
2. Prüfe, ob der genannte Template-Helfer noch existiert.
3. Achte nach einem Home-Assistant-Update auf eine neuere, noch unbestätigte Config-Entry-Schemaversion.
4. Starte einen neuen Scan.

Ein partieller Lauf löscht keine bestehende Benachrichtigung und setzt keine neue Event-Baseline.

## `parser_diagnostics` enthält Einträge

| Code | Bedeutung |
|---|---|
| `dynamic_entity_reference` | Entity-ID ist dynamisch und kann statisch nicht bewiesen werden |
| `invalid_static_entity_id` | statischer Wert hat kein gültiges Entity-ID-Format |
| `template_syntax_error` | Jinja-Syntax ist ungültig |

Dynamische Hinweise sind nicht zwingend Fehler im Template. Der Checker rät solche IDs bewusst nicht.

## Fehlende Entity wird nicht gemeldet

Mögliche Ursachen:

1. Sie besitzt noch einen Eintrag in der Entity Registry.
2. Ihre exakte ID steht in `ignored_entities`; prüfe `ignored_matches`.
3. Der Fund stammt aus einem Helfer mit dem gewählten Ignore-Label; prüfe `ignored_helper_sources` und `ignored_matches`.
4. Die Referenz ist dynamisch; prüfe `parser_diagnostics`.
5. Das Template stammt aus YAML, einer Automation, einem Script, Dashboard oder einer anderen nicht unterstützten Quelle.

## Helfer-Label wirkt nicht

- Das Label muss direkt an der vom Template-Helfer erzeugten Entity gesetzt sein.
- Geräte- und Bereichslabels werden nicht vererbt.
- Prüfe `ignored_helper_label.available`.
- Nach Löschen des gespeicherten Labels werden absichtlich keine Quellen mehr ausgeschlossen.

## Gespeichertes Label erscheint nur als ID

Das Label wurde wahrscheinlich gelöscht. Öffne die Optionen, entferne die alte Auswahl oder wähle ein vorhandenes Label. Der Scan läuft währenddessen konservativ ohne labelbasierte Ausschlüsse weiter.

## Benachrichtigung erscheint nicht

- Benachrichtigungen müssen aktiviert sein.
- `missing_entities` muss aktive Funde enthalten; ignorierte Funde allein erzeugen keine Benachrichtigung.
- Ein partieller Scan verändert die bestehende Benachrichtigung nicht.
- Ein identisches vollständiges Ergebnis erzeugt kein Duplikat.

## Fehlerbericht

1. Neueste öffentliche Version prüfen.
2. `template_entity_checker.scan_now` ausführen.
3. Sensorattribute und [Diagnostik](./diagnostics.md) prüfen.
4. Reproduktionsschritte und bereinigte Diagnostik in einem GitHub-Issue bereitstellen.

Keine Zugangsdaten, privaten URLs oder persönlichen Daten veröffentlichen.
