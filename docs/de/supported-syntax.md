# Unterstützte Syntax

Template Entity Checker extrahiert **statisch beweisbare** Entity-Referenzen aus Jinja-Templates. Das Template wird nie gerendert. Der Parser analysiert Syntax, Positionen und lokale Namensbindungen.

## Funktionsaufrufe

```jinja2
{{ states('sensor.wohnraum_beispieltemperatur') }}
{{ state_attr('sensor.wohnraum_beispieltemperatur', 'temperature') }}
{{ is_state('binary_sensor.terrassentuer_beispielkontakt', 'on') }}
{{ is_state_attr('sensor.heizkreis_beispielstatus', 'mode', 'heating') }}
{{ has_value('sensor.gartenhaus_beispielwert') }}
```

## `has_value` als Filter und Test

Home Assistant unterstützt `has_value` in drei Formen; alle drei werden geprüft:

```jinja2
{{ has_value('sensor.gartenhaus_beispielwert') }}
{{ 'sensor.gartenhaus_beispielwert' | has_value }}
{{ 'sensor.gartenhaus_beispielwert' is has_value }}
{{ 'sensor.gartenhaus_beispielwert' is not has_value }}
```

Auch geklammerte Stringliterale werden erkannt. Dynamische Operanden erzeugen eine Diagnose, aber keinen geratenen Fund.

```jinja2
{{ entity_variable | has_value }}
{{ entity_variable is has_value }}
```

## Dot-Notation

```jinja2
{{ states.sensor.wohnraum_beispieltemperatur.state }}
{{ states.binary_sensor.terrassentuer_beispielkontakt }}
```

## `expand()`

```jinja2
{{ expand(['sensor.wohnraum_beispieltemperatur', 'sensor.keller_beispieltemperatur']) }}
{{ expand('sensor.wohnraum_beispieltemperatur', 'sensor.keller_beispieltemperatur') }}
```

Literale Entity-IDs in Listen, Tupeln und mehreren Argumenten werden einzeln geprüft. Bei gemischten Containern werden statische Elemente geprüft; der dynamische Rest wird genau einmal als Diagnose gemeldet.

## Bewusst ignorierte Lookalikes

Folgendes ist keine statische Home-Assistant-Referenz:

- Funktionsnamen in normalem Text oder Jinja-Kommentaren
- Text innerhalb eines Stringliterals, der nur wie ein Aufruf aussieht
- gleichnamige Methoden auf anderen Objekten, etwa `helper.expand(...)`
- Makro-, Filterblock- und gewöhnliche Jinja-Testnamen
- lokal gebundene Namen anstelle der globalen Home-Assistant-Funktion

`has_value` ist die gezielte Ausnahme bei Jinja-Filtern und -Tests, weil Home Assistant diese Formen offiziell bereitstellt.

```jinja2
{# states('sensor.kommentar_beispiel') #}
{{ "states('sensor.string_beispiel')" }}
{{ helper.expand(['sensor.methoden_beispiel']) }}
{{ expand(['sensor.echter_beispielfund']) }}
```

## Lokale Variablen und Scopes

```jinja2
{{ states('sensor.vor_bindung_beispiel') }}
{% set states = local_helper %}
{{ states('sensor.nach_bindung_beispiel') }}
```

Der erste globale Aufruf bleibt erkennbar. Ab der lokalen Bindung wird `states` nicht mehr als Home-Assistant-Funktion behandelt. Bindungen in untergeordneten Scopes verstecken einen späteren globalen Aufruf außerhalb dieses Scopes nicht.

## Dynamische Referenzen

```jinja2
{{ states('sensor.' ~ raum) }}
{{ state_attr(entity_variable, 'temperature') }}
{{ expand(['sensor.wohnraum_beispieltemperatur', entity_variable]) }}
```

Dynamische IDs werden nicht aufgelöst. Sie erzeugen `dynamic_entity_reference`, aber niemals eine erfundene fehlende Entity.

## Duplikate und Fundstellen

Mehrere Vorkommen derselben ID werden zu einem Fund pro Helfer, Feld und Referenz gruppiert. `occurrence_count` und alle Zeilen-/Spaltenpositionen bleiben erhalten.
