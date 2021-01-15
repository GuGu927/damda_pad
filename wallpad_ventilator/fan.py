"""Provides functionality to interact with fans."""
from datetime import timedelta
import functools as ft
import logging
from typing import Optional

import voluptuous as vol

from homeassistant.const import (
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.loader import bind_hass
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    GREX,
    CONF_CONT,
    CONF_VENT,
    CONF_CONT_PORT,
    CONF_VENT_PORT,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "fan"
SCAN_INTERVAL = timedelta(seconds=1)

ENTITY_ID_FORMAT = DOMAIN + ".{}"

# Bitfield of features supported by the fan entity
SUPPORT_SET_SPEED = 1

SERVICE_SET_SPEED = "set_speed"

SPEED_OFF = "off"
SPEED_LOW = "low"
SPEED_MEDIUM = "medium"
SPEED_HIGH = "high"

ATTR_SPEED = "speed"
ATTR_SPEED_LIST = "speed_list"


@bind_hass
def is_on(hass, entity_id: str) -> bool:
    """Return if the fans are on based on the statemachine."""
    state = hass.states.get(entity_id)
    if ATTR_SPEED in state.attributes:
        return state.attributes[ATTR_SPEED] not in [SPEED_OFF, None]
    return state.state == STATE_ON


async def async_setup(hass, config: dict):
    return True


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up a config entry."""
    socket_client = hass.data[DOMAIN][config_entry.unique_id][GREX]
    ventilator_entity = GrexFan(socket_client)
    async_add_entities([ventilator_entity], True)


class GrexFan(ToggleEntity):
    """Representation of a fan."""

    def __init__(self, socket):
        """Initialize the Ventilator"""
        self._socket = socket
        self.speed = socket.speed

    def set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        raise NotImplementedError()

    async def async_set_speed(self, speed: str):
        """Set the speed of the fan."""
        if speed == SPEED_OFF:
            await self.async_turn_off()
        else:
            await self.hass.async_add_executor_job(self.set_speed, speed)

    # pylint: disable=arguments-differ
    def turn_on(self, speed: Optional[str] = None, **kwargs) -> None:
        """Turn on the fan."""
        raise NotImplementedError()

    # pylint: disable=arguments-differ
    async def async_turn_on(self, speed: Optional[str] = None, **kwargs):
        """Turn on the fan."""
        if speed == SPEED_OFF:
            await self.async_turn_off()
        else:
            await self.hass.async_add_executor_job(
                ft.partial(self.turn_on, speed, **kwargs)
            )

    @property
    def is_on(self):
        """Return true if the entity is on."""
        return self.speed not in [SPEED_OFF, None]

    @property
    def speed(self) -> Optional[str]:
        """Return the current speed."""
        return None

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return []

    @property
    def capability_attributes(self):
        """Return capability attributes."""
        if self.supported_features & SUPPORT_SET_SPEED:
            return {ATTR_SPEED_LIST: self.speed_list}
        return {}

    @property
    def state_attributes(self) -> dict:
        """Return optional state attributes."""
        data = {}
        supported_features = self.supported_features

        if supported_features & SUPPORT_SET_SPEED:
            data[ATTR_SPEED] = self.speed

        return data

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return 0
