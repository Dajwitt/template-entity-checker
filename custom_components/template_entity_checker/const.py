"""Constants for Template Entity Checker."""

from homeassistant.const import Platform

DOMAIN = "template_entity_checker"
NAME = "Template Entity Checker"
VERSION = "0.1.0"

PLATFORMS = [Platform.SENSOR]

CONF_SCAN_INTERVAL = "scan_interval"
CONF_NOTIFICATIONS = "notifications"
CONF_IGNORED_ENTITIES = "ignored_entities"

DEFAULT_SCAN_INTERVAL = 15
DEFAULT_NOTIFICATIONS = True
DEFAULT_IGNORED_ENTITIES = ""

SERVICE_SCAN_NOW = "scan_now"
EVENT_RESULT_CHANGED = "template_entity_checker_result_changed"
NOTIFICATION_ID = "template_entity_checker_missing_entities"
