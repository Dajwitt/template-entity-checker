# Aktion

## `template_entity_checker.scan_now`

Löst einen sofortigen Scan aller UI-basierten Template-Helfer aus.

### Parameter

Keine.

### Beispiel: Developer Tools

```yaml
action: template_entity_checker.scan_now
```

### Beispiel: Script

```yaml
script:
  template_check:
    alias: "Template-Check"
    sequence:
      - action: template_entity_checker.scan_now
```

### Serialisierung

Wenn ein Scan bereits läuft, wartet die ausgelöste Aktion auf die Sperre. Scans laufen nie parallel.