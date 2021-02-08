"""Support for wallpad lights."""
from homeassistant.components.light import DOMAIN, LightEntity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import NEW_LIGHT, DEVICE_UNIQUE
from .wallpad_device import WallpadDevice
from .gateway import get_wallpad


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up lights for Wallpad component."""
    gateway = get_wallpad(hass, config_entry)
    gateway.entities[DOMAIN + "load"] = False

    @callback
    def async_add_light(
            devices=gateway.api.lights() if gateway.api is not None else []):
        """Add light from Wallpad."""
        entities = []
        for device in devices:
            if (not gateway.entities[DOMAIN + "load"]
                    or device[DEVICE_UNIQUE] not in gateway.entities[DOMAIN]):
                entities.append(WallpadLight(device, gateway))

        if entities:
            async_add_entities(entities)

    gateway.listeners.append(
        async_dispatcher_connect(hass,
                                 gateway.async_signal_new_device(NEW_LIGHT),
                                 async_add_light))

    async_add_light()
    gateway.entities[DOMAIN + "load"] = True


class WallpadLight(WallpadDevice, LightEntity):
    """Representation of a Wallpad light."""
    TYPE = DOMAIN

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self.get_status()

    async def async_turn_on(self, **kwargs):
        """Turn on light."""
        self.set_status(True)

    async def async_turn_off(self, **kwargs):
        """Turn off light."""
        self.set_status(False)