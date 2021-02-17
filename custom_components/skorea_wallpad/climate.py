"""Support for wallpad climate devices."""
from typing import Optional

from homeassistant.components.climate import DOMAIN, ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    HVAC_MODE_FAN_ONLY,
    PRESET_AWAY,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import NEW_CLIMATE, DEVICE_UNIQUE, THERMO_MODE, THERMO_TARGET, THERMO_TEMP
from .wallpad_device import WallpadDevice
from .gateway import get_wallpad


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up climate for Wallpad component."""
    gateway = get_wallpad(hass, config_entry)
    gateway.entities[DOMAIN + "load"] = False

    @callback
    def async_add_climate(
        devices=get_wallpad(hass, config_entry).api.climates()
        if get_wallpad(hass, config_entry).api is not None
        and not isinstance(get_wallpad(hass, config_entry).api, bool) else []):
        """Add sensor from wallpad."""
        entities = []
        gateway = get_wallpad(hass, config_entry)
        for device in devices:
            if (not gateway.entities[DOMAIN + "load"]
                    or device[DEVICE_UNIQUE] not in gateway.entities[DOMAIN]):
                entities.append(WallpadThermostat(device, gateway))

        if entities:
            async_add_entities(entities)

    gateway.listeners.append(
        async_dispatcher_connect(hass,
                                 gateway.async_signal_new_device(NEW_CLIMATE),
                                 async_add_climate))

    async_add_climate()
    gateway.entities[DOMAIN + "load"] = True


class WallpadThermostat(WallpadDevice, ClimateEntity):
    """Representation of a deCONZ thermostat."""

    TYPE = DOMAIN

    def __init__(self, device, gateway):
        """Set up thermostat device."""
        super().__init__(device, gateway)
        self._features = SUPPORT_TARGET_TEMPERATURE

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._features

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode.\n
        Need to be one of HVAC_MODE_*.
        """
        status = self.get_status()
        if status is None: return HVAC_MODE_OFF
        return status.get(THERMO_MODE) if status.get(
            THERMO_MODE) != PRESET_AWAY else HVAC_MODE_FAN_ONLY

    @property
    def hvac_modes(self) -> list:
        """Return the list of available hvac operation modes."""
        mode = []
        for key in self.gateway.api.thermo_mode.keys():
            mode.append(key if key is not PRESET_AWAY else HVAC_MODE_FAN_ONLY)
        if mode is None:
            mode = [HVAC_MODE_HEAT, HVAC_MODE_OFF]
        return list(mode)

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set new target hvac mode."""
        if hvac_mode not in self.hvac_modes:
            raise ValueError(f"Unsupported HVAC mode {hvac_mode}")
        self.set_status({
            THERMO_MODE:
            hvac_mode if hvac_mode != HVAC_MODE_FAN_ONLY else PRESET_AWAY,
            THERMO_TARGET:
            self.target_temperature
        })

    # Temperature control

    @property
    def current_temperature(self) -> float:
        """Return the current temperature."""
        status = self.get_status()
        if status is not None: return status.get(THERMO_TEMP)

    @property
    def target_temperature(self) -> float:
        """Return the target temperature."""
        status = self.get_status()
        if status is not None: return status.get(THERMO_TARGET)

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if ATTR_TEMPERATURE not in kwargs:
            raise ValueError(f"Expected attribute {ATTR_TEMPERATURE}")
        self.set_status({
            THERMO_MODE: HVAC_MODE_HEAT,
            THERMO_TARGET: kwargs[ATTR_TEMPERATURE]
        })

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def target_temperature_high(self):
        return 30

    @property
    def target_temperature_low(self):
        return 10

    @property
    def target_temperature_step(self):
        return 1

    @property
    def device_state_attributes(self):
        """Return the state attributes of the thermostat."""
        attributes = dict(super().device_state_attributes)

        return attributes
