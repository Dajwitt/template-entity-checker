"""Tests for localized persistent notification content."""

from types import SimpleNamespace

from custom_components.template_entity_checker import notifications
from custom_components.template_entity_checker.notifications import (
    notification_message,
    notification_title,
    update_notification,
)


def findings():
    return {
        "sensor.missing": [
            {
                "helper": "Average humidity",
                "source_type": "template_helper",
                "source_id": "entry-1",
                "template_field": "state",
                "template_type": "sensor",
                "reference": "states('sensor.missing')",
                "occurrence_count": 1,
            }
        ]
    }


def test_german_notification_example_content():
    assert notification_title(1, "de-DE") == (
        "Template Entity Checker: 1 fehlende Entity"
    )
    message = notification_message(findings(), "de")
    assert "Template-Helfer" in message
    assert "Average humidity" in message
    assert "sensor.missing" in message
    assert "Sensorattribut `missing_entities`" in message


def test_english_plural_title():
    assert notification_title(2, "en") == "Template Entity Checker: 2 missing entities"


def test_notification_create_and_clean_dismiss(monkeypatch):
    created = []
    dismissed = []
    monkeypatch.setattr(
        notifications.persistent_notification,
        "async_create",
        lambda *args, **kwargs: created.append((args, kwargs)),
    )
    monkeypatch.setattr(
        notifications.persistent_notification,
        "async_dismiss",
        lambda *args: dismissed.append(args),
    )
    hass = SimpleNamespace(config=SimpleNamespace(language="de"))

    update_notification(hass, findings(), enabled=True)
    assert created[0][1]["notification_id"].startswith("template_entity_checker")

    update_notification(hass, {}, enabled=True)
    assert dismissed
