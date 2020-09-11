"""Support for Ritual Genie."""
from datetime import date
from datetime import timedelta
import logging

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
)
from homeassistant.exceptions import PlatformNotReady
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity, ToggleEntity
from homeassistant.util import Throttle
import voluptuous as vol

from . import rituals_api

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=5)

DEFAULT_DEVICE_CLASS = "visible"

# Sensor types are defined like so: Name, unit, icon
SENSOR_TYPES = {
    "battery_status": [
        "Battery status",
        "mdi:battery-70",
    ],
    "perfume_level": [
        "Perfume Level",
        "mdi:car-coolant-level",
    ],
    "perfume_name": [
        "Perfume name",
        "mdi:card-text-outline",
    ],
    "wifi_signal": [
        "WiFi Signal Strength",
        "mdi:wifi-strength-2",
    ],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the QNAP NAS sensor."""
    data = RitualsGenieData(config)
    data.update()

    # SunnyPortal is not available
    if not data.hubs:
        raise PlatformNotReady


    sensors = []
    for hub_name in data.hubs:
        _LOGGER.info("Discovered hub %s", hub_name)
        sensors.append(RitualsGenieBinarySensor(data.hubs, hub_name))
        for sensor_type in SENSOR_TYPES:
            sensors.append(RitualsGenieSensor(data.hubs, hub_name, sensor_type))

    add_entities(sensors)


class RitualsGenieData:
    """Class to interface with the API."""

    def __init__(self, config):
        """Initialize the API wrapper."""
        self._rituals_api = rituals_api.RitualsAPI(config.get(CONF_USERNAME), config.get(CONF_PASSWORD))
        self.hubs = {}

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update API information and store locally."""
        try:
            self._rituals_api._getHubs()
            self.hubs = self._rituals_api.hubs
        except:  # noqa: E722 pylint: disable=bare-except
            _LOGGER.exception("Failed to fetch stats from sunny portal")


class RitualsGenieBinarySensor(ToggleEntity):
    """Implementation of the Rituals Genie binary sensor."""

    def __init__(self, data, hub_name):
        """Initialize the sensor."""
        self.data = data
        self._hub_name = hub_name
        self._state = None
        self.entity_id = f"ritualsgenie.{self._hub_name}_status".lower()

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Status"

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self.data[self._hub_name]["attributes"]["fanc"]

    @property
    def device_class(self):
        """Return the class of this sensor."""
        return DEFAULT_DEVICE_CLASS

    def update(self):
        """Get the latest data from ISS API and updates the states."""
        self.data.update()


class RitualsGenieSensor(Entity):
    """Base class for a Rituals Genie sensor."""

    def __init__(self, data, hub_name, sensor_type):
        """Initialize the sensor."""
        self._hub_name = hub_name
        self.data = data
        self.type = sensor_type
        self.entity_id = f"ritualsgenie.{self._hub_name}_{sensor_type}".lower()
        self._name = SENSOR_TYPES[sensor_type][0]
        self._icon = SENSOR_TYPES[sensor_type][1]
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor, if any."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self):
        """Get the latest data for the states."""
        self.data.update()
        if self.type == "battery_status":
            self._state = self.data[self._hub_name]["sensors"]["battc"]["title"]
        elif self.type == "perfume_level":
            self._state = self.data[self._hub_name]["sensors"]["fillc"]["title"]
        elif self.type == "perfume_name":
            self._state = self.data[self._hub_name]["sensors"]["rfidc"]["title"]
        elif self.type == "wifi_signal":
            self._state = self.data[self._hub_name]["sensors"]["wific"]["title"]


