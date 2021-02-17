"""Support for wallpad sensors."""
from homeassistant.components.sensor import DOMAIN
from homeassistant.const import (ATTR_TEMPERATURE, DEVICE_CLASS_POWER,
                                 DEVICE_CLASS_TEMPERATURE,
                                 ENERGY_KILO_WATT_HOUR, POWER_WATT,
                                 TEMP_CELSIUS, VOLUME_CUBIC_METERS)
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import NEW_SENSOR, DEVICE_UNIQUE, WPD_EVSENSOR
from .wallpad_device import WallpadDevice
from .gateway import get_wallpad

DEVICE_CLASS = {
    "power": DEVICE_CLASS_POWER,
    "temperature": DEVICE_CLASS_TEMPERATURE,
}

ICON = {
    WPD_EVSENSOR: "mdi:elevator",
}

UNIT_OF_MEASUREMENT = {
    "consumption": ENERGY_KILO_WATT_HOUR,
    "power": POWER_WATT,
    "temperature": TEMP_CELSIUS,
    "gas": VOLUME_CUBIC_METERS,
    "water": VOLUME_CUBIC_METERS,
    WPD_EVSENSOR: "층",
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up sensor for Wallpad component."""
    gateway = get_wallpad(hass, config_entry)
    gateway.entities[DOMAIN + "load"] = False

    @callback
    def async_add_sensor(
        devices=get_wallpad(hass, config_entry).api.sensors()
        if get_wallpad(hass, config_entry).api is not None
        and not isinstance(get_wallpad(hass, config_entry).api, bool) else []):
        """Add sensor from wallpad."""
        entities = []
        gateway = get_wallpad(hass, config_entry)
        for device in devices:
            if (not gateway.entities[DOMAIN + "load"]
                    or device[DEVICE_UNIQUE] not in gateway.entities[DOMAIN]):
                entities.append(WallpadSensor(device, gateway))

        if entities:
            async_add_entities(entities)

    gateway.listeners.append(
        async_dispatcher_connect(hass,
                                 gateway.async_signal_new_device(NEW_SENSOR),
                                 async_add_sensor))

    async_add_sensor()
    gateway.entities[DOMAIN + "load"] = True


class WallpadSensor(WallpadDevice):
    """Representation of a deCONZ sensor."""

    TYPE = DOMAIN

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.get_status()

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON.get(self.device_type, ICON.get(self.device_room))

    @property
    def device_class(self):
        """Return the class of the sensor."""
        return DEVICE_CLASS.get(self.device_type,
                                DEVICE_CLASS.get(self.device_room))

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this sensor."""
        return UNIT_OF_MEASUREMENT.get(
            self.device_type, UNIT_OF_MEASUREMENT.get(self.device_room))
