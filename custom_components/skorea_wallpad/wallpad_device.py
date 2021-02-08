from homeassistant.helpers.entity import Entity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import (DOMAIN, DEVICE_INFO, DEVICE_UNIQUE, DEVICE_GET, DEVICE_SET,
                    DEVICE_REG, DEVICE_UNREG, DEVICE_ID, DEVICE_NAME,
                    DEVICE_SUB, DEVICE_ROOM, DEVICE_TYPE, WPD_MAIN,
                    WPD_DOORLOCK, WPD_EV, WPD_FAN, WPD_GAS, WPD_LIGHT,
                    WPD_MOTION, WPD_SWITCH, WPD_THERMOSTAT, WPD_MAIN_LIST)


class WallpadBase:
    def __init__(self, device, gateway):
        self._device = device
        self.gateway = gateway
        self.register = self._device[DEVICE_REG]
        self.unregister = self._device[DEVICE_UNREG]
        self.sub_id = self._device[DEVICE_SUB]
        self.info = self._device[DEVICE_INFO]
        self.device_id = self.info[DEVICE_ID]
        self.device_name = self.info[DEVICE_NAME]
        self.device_room = self.info[DEVICE_ROOM]
        self.device_type = self.info[DEVICE_TYPE]

    def set_status(self, value):
        self._device[DEVICE_SET](self.device_id, self.sub_id, value)

    def get_status(self):
        return self._device[DEVICE_GET](self.device_id, self.sub_id)

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._device[DEVICE_UNIQUE]

    @property
    def device_info(self):
        """Return device registry information for this entity."""
        if (self.device_type in WPD_MAIN_LIST):
            return {
                "connections": {(DOMAIN, self.unique_id)},
                "identifiers": {(DOMAIN, self.gateway.host)},
            }
        return {
            "connections": {(DOMAIN, self.unique_id)},
            "identifiers":
            {(DOMAIN,
              f"{self.gateway.brand}_{self.gateway.api.brand}_{self.device_room}"
              )},
            "manufacturer": self.gateway.brand,
            "model": f"{self.gateway.api.brand}_{self.gateway.api.version}",
            "name": f"{self.gateway.api.brand_name} {self.device_room}",
            "sw_version": self.gateway.api.version,
            "via_device": (DOMAIN, self.gateway.host),
        }


class WallpadDevice(WallpadBase, Entity):
    """Defines a Wallpad Device entity."""
    TYPE = ""

    def __init__(self, device, gateway):
        """Initialize the instance."""
        super().__init__(device, gateway)
        if self.unique_id not in self.gateway.entities[self.TYPE]:
            self.gateway.entities[self.TYPE].add(self.unique_id)

    @property
    def entity_registry_enabled_default(self):
        return True

    async def async_added_to_hass(self):
        """Subscribe to device events."""
        self.register(self.unique_id, self.async_update_callback)
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Disconnect device object when removed."""
        self.unregister(self.unique_id)
        self.gateway.entities[self.TYPE].remove(self.unique_id)

    @callback
    def async_update_callback(self):
        """Update the device's state."""
        self.async_write_ha_state()

    @property
    def available(self):
        """Return True if device is available."""
        return self.gateway.available

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self.device_name

    @property
    def should_poll(self) -> bool:
        """No polling needed for this device."""
        return False

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        attr = {
            DEVICE_UNIQUE: self.unique_id,
            DEVICE_ROOM: self.device_room,
            DEVICE_TYPE: self.device_type
        }
        return attr
