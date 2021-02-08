"""Config flow for KoreAssistant."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_entry_flow
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, BRAND, CONF_SOCKET, CONF_PORT, DEFAULT_SOCKET, DEFAULT_PORT, SCAN_INTERVAL, SCAN_LIST, SEND_INTERVAL


async def _async_has_devices(hass) -> bool:
    """Return if there are devices that can be discovered."""
    # TODO Check if there are any devices that can be discovered in the network.
    return False


config_entry_flow.register_discovery_flow(DOMAIN, BRAND, _async_has_devices,
                                          config_entries.CONN_CLASS_LOCAL_PUSH)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for KoreAssistant."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_SOCKET])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input[CONF_SOCKET],
                                           data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_SOCKET):
                cv.string,
                vol.Required(CONF_PORT, default=DEFAULT_PORT):
                cv.port,
            }),
            errors=errors,
        )

    async def async_step_import(self, user_input=None):
        """Handle configuration by yaml file."""
        await self.async_set_unique_id(user_input[CONF_SOCKET])
        for entry in self._async_current_entries():
            if entry.unique_id == self.unique_id:
                self.hass.config_entries.async_update_entry(entry,
                                                            data=user_input)
                self._abort_if_unique_id_configured()
        return self.async_create_entry(title=user_input[CONF_SOCKET],
                                       data=user_input)
