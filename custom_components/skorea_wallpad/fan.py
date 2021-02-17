"""Support for wallpad fans."""
from homeassistant.components.climate.const import (FAN_MEDIUM, FAN_OFF,
                                                    FAN_ON)
from homeassistant.components.fan import (
    DOMAIN,
    SPEED_HIGH,
    SPEED_LOW,
    SPEED_MEDIUM,
    SPEED_OFF,
    SUPPORT_SET_SPEED,
    FanEntity,
)
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import FAN_SPEED, NEW_FAN, DEVICE_UNIQUE, DEVICE_STATE
from .wallpad_device import WallpadDevice
from .gateway import get_wallpad


async def async_setup_entry(hass, config_entry, async_add_entities) -> None:
    """Set up fan for Wallpad component."""
    gateway = get_wallpad(hass, config_entry)
    gateway.entities[DOMAIN + "load"] = False

    @callback
    def async_add_fan(
        devices=get_wallpad(hass, config_entry).api.fans()
        if get_wallpad(hass, config_entry).api is not None
        and not isinstance(get_wallpad(hass, config_entry).api, bool) else []):
        """Add fan from wallpad."""
        entities = []
        gateway = get_wallpad(hass, config_entry)
        for device in devices:
            if (not gateway.entities[DOMAIN + "load"]
                    or device[DEVICE_UNIQUE] not in gateway.entities[DOMAIN]):
                entities.append(WallpadFan(device, gateway))

        if entities:
            async_add_entities(entities)

    gateway.listeners.append(
        async_dispatcher_connect(hass,
                                 gateway.async_signal_new_device(NEW_FAN),
                                 async_add_fan))

    async_add_fan()
    gateway.entities[DOMAIN + "load"] = True


class WallpadFan(WallpadDevice, FanEntity):
    """Representation of a deCONZ fan."""

    TYPE = DOMAIN

    def __init__(self, device, gateway) -> None:
        """Set up fan."""
        super().__init__(device, gateway)
        self._features = SUPPORT_SET_SPEED

    @property
    def is_on(self) -> bool:
        """Return true if fan is on."""
        status = self.get_status()
        if status is not None: return FAN_ON == status.get(DEVICE_STATE)

    @property
    def speed(self) -> int:
        """Return the current speed."""
        status = self.get_status()
        if status is not None:
            return status.get(FAN_SPEED) if FAN_ON == status.get(
                DEVICE_STATE) else SPEED_OFF

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return list([SPEED_OFF, SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH])

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return self._features

    async def async_set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        state = FAN_OFF if speed == SPEED_OFF else FAN_ON
        self.set_status({DEVICE_STATE: state, FAN_SPEED: speed})

    async def async_turn_on(self, speed: str = FAN_MEDIUM, **kwargs) -> None:
        """Turn on fan."""
        state = FAN_OFF if speed == SPEED_OFF else FAN_ON
        self.set_status({DEVICE_STATE: state, FAN_SPEED: speed})

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off fan."""
        self.set_status({DEVICE_STATE: FAN_OFF, FAN_SPEED: SPEED_OFF})
