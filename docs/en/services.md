# Action

## `template_entity_checker.scan_now`

Immediately scans every UI-created Template Helper.

### Parameters

None.

### Developer Tools example

```yaml
action: template_entity_checker.scan_now
```

### Script example

```yaml
script:
  template_check:
    alias: "Template check"
    sequence:
      - action: template_entity_checker.scan_now
```

### Serialization

If another scan is active, the action waits for the scan lock. Scans never run in parallel.
