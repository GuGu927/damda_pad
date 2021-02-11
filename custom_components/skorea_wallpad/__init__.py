"""The KoreAssistant integration."""
import asyncio
from homeassistant.helpers.dispatcher import async_dispatcher_connect
import logging

from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from .gateway import WallpadGateway

from .const import (DOMAIN, PLATFORMS, BRAND, RELOAD_SIGNAL, CONF_SOCKET,
                    CONF_HOST)

_LOGGER = logging.getLogger(__name__)


@callback
async def async_reload_gateway(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the KoreAssistant component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up KoreAssistant from a config entry."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    gateway = WallpadGateway(hass, entry)
    await gateway.async_update_device_registry()
    await gateway.async_get_entity_registry()
    connect = gateway.connect()
    if connect:
        gateway.initialize()
        hass.data[DOMAIN][entry.unique_id] = gateway
        for component in PLATFORMS:
            hass.async_create_task(
                hass.config_entries.async_forward_entry_setup(
                    entry, component))
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, gateway.stop)
    else:
        _LOGGER.info(f"[{BRAND}] 컴포넌트를 불러올 수 없습니다.")

    async_dispatcher_connect(hass, RELOAD_SIGNAL, async_reload_gateway)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(await asyncio.gather(*[
        hass.config_entries.async_forward_entry_unload(entry, component)
        for component in PLATFORMS
    ]))
    if unload_ok:
        hass.data[DOMAIN][entry.unique_id].stop(False)
        hass.data[DOMAIN].pop(entry.unique_id)

    return unload_ok


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:

        new = {**config_entry.data}
        new[CONF_HOST] = new[CONF_SOCKET]
        new.pop(CONF_SOCKET)

        config_entry.data = {**new}

        config_entry.version = 2

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    return True