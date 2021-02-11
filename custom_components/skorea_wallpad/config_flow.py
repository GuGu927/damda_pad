"""Config flow for KoreAssistant."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_entry_flow
import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback

from .const import OPTION_LIST, DOMAIN, BRAND, CONF_SOCKET, CONF_HOST, CONF_PORT, DEFAULT_SOCKET, DEFAULT_HOST, DEFAULT_PORT, WPD_MAIN_LIST


async def _async_has_devices(hass) -> bool:
    """Return if there are devices that can be discovered."""
    # TODO Check if there are any devices that can be discovered in the network.
    return False


config_entry_flow.register_discovery_flow(DOMAIN, BRAND, _async_has_devices,
                                          config_entries.CONN_CLASS_LOCAL_PUSH)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for KoreAssistant."""

    VERSION = 2

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input[CONF_HOST],
                                           data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, description=DEFAULT_HOST):
                cv.string,
                vol.Required(CONF_PORT, default=DEFAULT_PORT):
                cv.port,
            }),
            errors=errors,
        )

    async def async_step_import(self, user_input=None):
        """Handle configuration by yaml file."""
        await self.async_set_unique_id(user_input[CONF_HOST])
        for entry in self._async_current_entries():
            if entry.unique_id == self.unique_id:
                self.hass.config_entries.async_update_entry(entry,
                                                            data=user_input)
                self._abort_if_unique_id_configured()
        return self.async_create_entry(title=user_input[CONF_HOST],
                                       data=user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow for Wallpad Ventilator."""
    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        conf = self.config_entry
        if conf.source == config_entries.SOURCE_IMPORT:
            return self.async_show_form(step_id="init", data_schema=None)
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = {}
        data_list = [CONF_HOST, CONF_PORT]
        for name, default, validation in OPTION_LIST.get(
                conf.data.get("wallpad", "default"), OPTION_LIST["default"]):
            to_default = conf.data.get(name, default) if name in data_list else conf.options.get(name, default)
            key = vol.Required(name, default=to_default)
            options_schema[key] = validation
        return self.async_show_form(step_id="init",
                                    data_schema=vol.Schema(options_schema))
