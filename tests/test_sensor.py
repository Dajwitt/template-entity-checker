"""Result sensor tests."""

from types import SimpleNamespace

from custom_components.template_entity_checker.sensor import TemplateEntityCheckerSensor


class Coordinator:
    def __init__(self):
        self.data = {
            "status": "missing_entities",
            "complete": True,
            "missing_entities": {"sensor.missing": []},
            "ignored_matches": {},
            "parser_diagnostics": [],
            "load_errors": [],
            "template_types_scanned": ["sensor"],
            "last_scan": "2026-07-23T12:00:00+00:00",
        }
        self.last_update_success = True
        self.last_exception = None
        self.scan_interval_minutes = 15
        self.ignored_entities = []

    def async_add_listener(self, update_callback, context=None):
        return lambda: None


def test_sensor_state_and_attributes():
    sensor = TemplateEntityCheckerSensor(
        Coordinator(), SimpleNamespace(entry_id="entry-1")
    )
    assert sensor.native_value == 1
    attributes = sensor.extra_state_attributes
    assert attributes["missing_entities"] == {"sensor.missing": []}
    assert attributes["complete"] is True
    assert attributes["load_errors"] == []
    assert attributes["template_types_scanned"] == ["sensor"]
