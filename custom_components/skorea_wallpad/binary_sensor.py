"""Support for wallpad binary_sensors."""
from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_MOTION,
    DOMAIN,
    BinarySensorEntity,
)
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import NEW_BSENSOR, DEVICE_UNIQUE
from .wallpad_device import WallpadDevice
from .gateway import get_wallpad


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up binary_sensor for Wallpad component."""
    gateway = get_wallpad(hass, config_entry)
    gateway.entities[DOMAIN + "load"] = False

    @callback
    def async_add_sensor(devices=gateway.api.binary_sensors()
                         if gateway.api is not None else []):
        """Add binary_sensor from wallpad."""
        entities = []
        for device in devices:
            if (not gateway.entities[DOMAIN + "load"]
                    or device[DEVICE_UNIQUE] not in gateway.entities[DOMAIN]):
                entities.append(WallpadBinarySensor(device, gateway))

        if entities:
            async_add_entities(entities)

    gateway.listeners.append(
        async_dispatcher_connect(hass,
                                 gateway.async_signal_new_device(NEW_BSENSOR),
                                 async_add_sensor))

    async_add_sensor()
    gateway.entities[DOMAIN + "load"] = True


class WallpadBinarySensor(WallpadDevice, BinarySensorEntity):
    """Representation of a deCONZ binary sensor."""

    TYPE = DOMAIN

    @property
    def is_on(self):
        """Return true if sensor is on."""
        return self.get_status()

    @property
    def device_class(self):
        """Return the class of the sensor."""
        return DEVICE_CLASS_MOTION