"""Config flow for Wallpad Ventilator."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import config_entry_flow
import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_CONT,
    CONF_VENT,
    CONF_CONT_PORT,
    CONF_VENT_PORT,
    INTEGRATION,
)

DEFAULT_IP = "192.168.x.x"
DEFAULT_PORT = 8899


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=INTEGRATION, data=user_input)

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        input_schema = {
            vol.Required(CONF_CONT, default=DEFAULT_IP): cv.string,
            vol.Required(CONF_CONT_PORT, default=DEFAULT_PORT): cv.port,
            vol.Required(CONF_VENT, default=DEFAULT_IP): cv.string,
            vol.Required(CONF_VENT_PORT, default=DEFAULT_PORT): cv.port,
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(input_schema),
            errors=errors,
        )

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

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CONT,
                        default=conf.options.get(CONF_CONT)
                        if conf.options.get(CONF_CONT) is not None
                        else conf.data.get(CONF_CONT),
                    ): cv.string,
                    vol.Required(
                        CONF_CONT_PORT,
                        default=conf.options.get(CONF_CONT_PORT)
                        if conf.options.get(CONF_CONT_PORT) is not None
                        else conf.data.get(CONF_CONT_PORT),
                    ): cv.port,
                    vol.Required(
                        CONF_VENT,
                        default=conf.options.get(CONF_VENT)
                        if conf.options.get(CONF_VENT) is not None
                        else conf.data.get(CONF_VENT),
                    ): cv.string,
                    vol.Required(
                        CONF_VENT_PORT,
                        default=conf.options.get(CONF_VENT_PORT)
                        if conf.options.get(CONF_VENT_PORT) is not None
                        else conf.data.get(CONF_VENT_PORT),
                    ): cv.port,
                }
            ),
        )