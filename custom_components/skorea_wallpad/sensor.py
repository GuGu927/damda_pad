"""Support for wallpad sensors."""
from homeassistant.components.sensor import DOMAIN
from homeassistant.const import (
    ATTR_TEMPERATURE,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_TEMPERATURE,
    ENERGY_KILO_WATT_HOUR,
    POWER_WATT,
    TEMP_CELSIUS,
)
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import NEW_SENSOR, DEVICE_UNIQUE
from .wallpad_device import WallpadDevice
from .gateway import get_wallpad

DEVICE_CLASS = {
    "Power": DEVICE_CLASS_POWER,
    "Temperature": DEVICE_CLASS_TEMPERATURE,
}

UNIT_OF_MEASUREMENT = {
    "Consumption": ENERGY_KILO_WATT_HOUR,
    "Power": POWER_WATT,
    "Temperature": TEMP_CELSIUS,
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up sensor for Wallpad component."""
    gateway = get_wallpad(hass, config_entry)
    gateway.entities[DOMAIN + "load"] = False

    @callback
    def async_add_sensor(
            devices=gateway.api.sensors() if gateway.api is not None else []):
        """Add sensor from wallpad."""
        entities = []
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
    def device_class(self):
        """Return the class of the sensor."""
        return DEVICE_CLASS.get(type(self._device))

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this sensor."""
        return UNIT_OF_MEASUREMENT.get(type(self._device))
