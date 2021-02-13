"""Constants for the KoreAssistant integration."""
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
from homeassistant.components.fan import DOMAIN as FAN_DOMAIN
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.components.climate.const import (
    FAN_OFF,
    FAN_ON,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    PRESET_AWAY,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)

VERSION = "1.8"
BRAND = "SmartKoreAssistant"
DOMAIN = "skorea_wallpad"
NAME = "SKA Wallpad"
MODEL = "ska-wallpad"
RELOAD_SIGNAL = "reload_wallpad_gateway"
PLATFORMS = [
    BINARY_SENSOR_DOMAIN, CLIMATE_DOMAIN, FAN_DOMAIN, LIGHT_DOMAIN,
    SENSOR_DOMAIN, SWITCH_DOMAIN
]

CONF_SOCKET, DEFAULT_SOCKET = "socket", "192.168.x.x"
CONF_HOST, DEFAULT_HOST = "host", "192.168.x.x or /dev/ttyXXX"
CONF_PORT, DEFAULT_PORT = "port", 8899
CONF_WPD = "wallpad"

WPD_MAIN = "wallpad"
WPD_LIGHT = "light"
WPD_SWITCH = "outlet"
WPD_THERMOSTAT = "thermostat"
WPD_DOORLOCK = "doorlock"
WPD_FAN = "fan"
WPD_GAS = "gas"
WPD_EV = "elevator"
WPD_EVSENSOR = "evsensor"
WPD_MOTION = "motion"
WPD_LIGHTBREAK = "lightbreak"
WPD_MAIN_LIST = [
    WPD_GAS, WPD_EV, WPD_DOORLOCK, WPD_FAN, WPD_MOTION, WPD_LIGHTBREAK,
    WPD_EVSENSOR
]

NEW_LIGHT = "lights"
NEW_SWITCH = "switchs"
NEW_SENSOR = "sensors"
NEW_BSENSOR = "binary_sensors"
NEW_FAN = "fans"
NEW_CLIMATE = "climates"

DEFAULT_MODE = "Off"
DEFAULT_TEMP = 10

FAN_STATE = "state"
FAN_SPEED = "speed"
FAN_MODE = "mode"

THERMO_HEAT = HVAC_MODE_HEAT
THERMO_AWAY = PRESET_AWAY
THERMO_OFF = HVAC_MODE_OFF
THERMO_MODE = "mode"
THERMO_TARGET = "target"
THERMO_TEMP = "temperature"

ENTITY_MAP = {
    WPD_LIGHT: LIGHT_DOMAIN,
    WPD_LIGHTBREAK: LIGHT_DOMAIN,
    WPD_SWITCH: SWITCH_DOMAIN,
    WPD_THERMOSTAT: CLIMATE_DOMAIN,
    WPD_GAS: SWITCH_DOMAIN,
    WPD_EV: SWITCH_DOMAIN,
    WPD_FAN: FAN_DOMAIN,
    WPD_MOTION: BINARY_SENSOR_DOMAIN,
    WPD_DOORLOCK: SWITCH_DOMAIN
}

TICK = "tick"
DEVICE_ID = "device_id"
DEVICE_NAME = "device_name"
DEVICE_ROOM = "device_room"
DEVICE_UNIQUE = "unique_id"
DEVICE_TYPE = "device_type"
DEVICE_SUB = "sub_id"
DEVICE_STATE = "state"
DEVICE_INFO = "device_info"
DEVICE_SET = "set"
DEVICE_GET = "get"
DEVICE_UPDATE = "update"
DEVICE_REG = "register"
DEVICE_UNREG = "unregister"
DEVICE_TRY = "try"

SIGNAL = {
    LIGHT_DOMAIN: NEW_LIGHT,
    SWITCH_DOMAIN: NEW_SWITCH,
    CLIMATE_DOMAIN: NEW_CLIMATE,
    FAN_DOMAIN: NEW_FAN,
    BINARY_SENSOR_DOMAIN: NEW_BSENSOR,
    SENSOR_DOMAIN: NEW_SENSOR,
}

CMD_SCAN = "조회"
CMD_STATUS = "상태"
CMD_CHANGE = "제어"
CMD_ON = "켜짐"
CMD_OFF = "꺼짐"
CMD_DETECT = "감지"


def int_between(min_int, max_int):
    """Return an integer between 'min_int' and 'max_int'."""
    return vol.All(vol.Coerce(int), vol.Range(min=min_int, max=max_int))


SCAN_LIST = [WPD_LIGHT, WPD_SWITCH, WPD_THERMOSTAT, WPD_GAS, WPD_FAN]
SEND_RETRY = 5
SEND_INTERVAL = 300
SCAN_INTERVAL = 6 * 60
OPT_SCAN_LIST = "scan_list"
OPT_SCAN_INT = "scan_interval"
OPT_SEND_RETRY = "send_retry"
OPT_SEND_INT = "send_interval"
OPT_DEFAULT = [(CONF_HOST, DEFAULT_HOST, cv.string),
               (CONF_PORT, DEFAULT_PORT, cv.port),
               (OPT_SEND_RETRY, SEND_RETRY, int_between(1, 20)),
               (OPT_SEND_INT, SEND_INTERVAL, int_between(10, 2000))]
OPT_KOCOM = [(OPT_SCAN_LIST, SCAN_LIST, cv.multi_select(SCAN_LIST)),
             (OPT_SCAN_INT, SCAN_INTERVAL, int_between(1, 20))]
OPTION_LIST = {"default": OPT_DEFAULT, "kocom": OPT_DEFAULT + OPT_KOCOM}
