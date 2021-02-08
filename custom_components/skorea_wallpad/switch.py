"""Support for wallpad lights."""
from homeassistant.components.switch import DOMAIN, SwitchEntity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import NEW_SWITCH, DEVICE_UNIQUE, WPD_EV, WPD_GAS, WPD_SWITCH
from .wallpad_device import WallpadDevice
from .gateway import get_wallpad

ICON = {
    WPD_SWITCH: "mdi:power-socket-eu",
    WPD_EV: "mdi:elevator",
    WPD_GAS: "mdi:gas-cylinder"
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up switchs for Wallpad component."""
    gateway = get_wallpad(hass, config_entry)
    gateway.entities[DOMAIN + "load"] = False

    @callback
    def async_add_switch(
            devices=gateway.api.switchs() if gateway.api is not None else []):
        """Add switch from Wallpad."""
        entities = []
        for device in devices:
            if (not gateway.entities[DOMAIN + "load"]
                    or device[DEVICE_UNIQUE] not in gateway.entities[DOMAIN]):
                entities.append(WallpadSwitch(device, gateway))

        if entities:
            async_add_entities(entities)

    gateway.listeners.append(
        async_dispatcher_connect(hass,
                                 gateway.async_signal_new_device(NEW_SWITCH),
                                 async_add_switch))

    async_add_switch()
    gateway.entities[DOMAIN + "load"] = True


class WallpadSwitch(WallpadDevice, SwitchEntity):
    """Representation of a Wallpad outlet."""
    TYPE = DOMAIN

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return ICON.get(self.device_type)

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self.get_status()

    async def async_turn_on(self, **kwargs):
        """Turn on switch."""
        self.set_status(True)

    async def async_turn_off(self, **kwargs):
        """Turn off switch."""
        self.set_status(False)
