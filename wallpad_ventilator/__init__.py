"""The Wallpad Ventilator integration."""
import asyncio
import socket
import logging
import threading

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry, ConfigError
import homeassistant.helpers.config_validation as cv

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

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            vol.Schema({vol.Required(CONF_CONT): cv.string}),
            vol.Schema({vol.Required(CONF_CONT_PORT): cv.port}),
            vol.Schema({vol.Required(CONF_VENT): cv.string}),
            vol.Schema({vol.Required(CONF_VENT_PORT): cv.port}),
        )
    },
    extra=vol.ALLOW_EXTRA,
)

GREX_MODE = {"0100": "auto", "0200": "manual", "0300": "sleep", "0000": "off"}
GREX_SPEED = {"0101": "low", "0202": "medium", "0303": "high", "0000": "off"}


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Wallpad Ventilator component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Wallpad Ventilator from a config entry."""
    # TODO Store an API object for your platforms to access
    rs485socket = Ventilator(
        cont=entry.options.get(CONF_CONT),
        cont_port=entry.options.get(CONF_CONT_PORT),
        vent=entry.options.get(CONF_VENT),
        vent_port=entry.options.get(CONF_VENT_PORT),
    )
    if not rs485socket.isConnected:
        _LOGGER.info("Not Conncted. Check socket connection.")
        raise ConfigError()

    hass.data[DOMAIN] = {entry.unique_id: {GREX: rs485socket}}
    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    # unload_ok = all(
    #     await asyncio.gather(
    #         *[
    #             hass.config_entries.async_forward_entry_unload(entry, component)
    #             for component in PLATFORMS
    #         ]
    #     )
    # )
    # if unload_ok:
    #     hass.data[DOMAIN].pop(entry.entry_id)

    # return unload_ok
    return True


class Ventilator:
    def __init__(
        self,
        cont=None,
        cont_port=None,
        vent=None,
        vent_port=None,
    ):
        """Initialize the Ventilator"""
        self.controller_ip = cont
        self.controlle_port = cont_port
        self.ventilator_ip = vent
        self.ventilator_port = vent_port

        self._name = "ventilator_grex"
        self._mode = "off"
        self._speed = "off"

        self.status = {
            "controller": {"speed": "off", "mode": "off"},
            "ventilator": {"speed": "off"},
        }

        self.connected = {"controller": False, "ventilator": False}
        self.controller = self.connect(
            "controller", self.controller_ip, self.controlle_port
        )
        self.ventilator = self.connect(
            "ventilator", self.ventilator_ip, self.ventilator_port
        )
        if self.controller and self.ventilator:
            self._cont = threading.Thread(
                target=self.poll, args=(self.controller, "controller", 11)
            )
            self._cont.daemon = True
            self._cont.start()
            self._vent = threading.Thread(
                target=self.poll, args=(self.ventilator, "ventilator", 12)
            )
            self._vent.daemon = True
            self._vent.start()

    @property
    def isConnected(self):
        return self.connected["controller"] & self.connected["ventilator"]

    @property
    def name(self) -> str:
        return self._name

    @property
    def mode(self):
        return self._mode

    @property
    def speed(self) -> str:
        return self._speed

    def control(self, s):
        self.status["ventilator"]["speed"] = s

    def set_mode(self, s):
        if self._mode != s:
            _LOGGER.info(f"환기장치 유니트 => 상태[{s}]")
            self._mode = s

    def set_speed(self, s):
        if self._speed != s:
            _LOGGER.info(f"환기장치 유니트 => 속도[{s}]")
            self._speed = s

    def set_cont(self, s, m):
        if (
            self.status["controller"]["speed"] != s
            or self.status["controller"]["mode"] != m
        ):
            _LOGGER.info(f"환기장치 컨트롤러 => 모드[{m}] 속도[{s}]")
            self.status["controller"]["speed"] = s
            self.status["controller"]["mode"] = m

    def write(self, packet, device, name):
        try:
            device.send(bytearray.fromhex(packet))
        except:
            self.connected[name] = False

    def read(self, device, name):
        try:
            return device.recv(1)
        except:
            self.connected[name] = False

    def poll(self, soc, packet_name, packet_len):
        """Get serial data from socket."""
        buf = []
        start_flag = False
        try:
            while packet_name is not None and packet_len is not None:
                row_data = self.read(soc, packet_name)
                hex_d = row_data.hex()
                # _LOGGER.info(f"{packet_name}: {hex_d}")
                start_hex = ""
                if packet_name == "ventilator":
                    start_hex = "d1"
                elif packet_name == "controller":
                    start_hex = "d0"
                if hex_d == start_hex:
                    start_flag = True
                if start_flag == True:
                    buf.append(hex_d)

                if len(buf) >= packet_len:
                    joindata = "".join(buf)
                    chksum = self.validate_checksum(joindata, packet_len - 1)
                    if chksum[0]:
                        self.packet_parsing(joindata, packet_name)
                    buf = []
                    start_flag = False
                if not self.connected[packet_name]:
                    _LOGGER.info(f"[Ventilator] 서버연결 Error {packet_name}")
                    break
        except:
            if not self.connected[packet_name]:
                _LOGGER.info(f"[Ventilator] 서버연결 Error {packet_name}")

    def connect(self, name, server, port):
        soc = socket.socket()
        soc.settimeout(10)
        try:
            soc.connect((server, int(port)))
        except Exception as e:
            _LOGGER.info(f"소켓에 연결할 수 없습니다.[{e}][{server}:{port}]")
            return False
        soc.settimeout(None)
        _LOGGER.info(f"소켓에 연결했습니다. {name} {server} {port}")
        self.connected[name] = True
        return soc

    def packet_parsing(self, packet, packet_name):
        p_prefix = packet[:4]
        # _LOGGER.info(f"{packet_name} : {packet}")

        if p_prefix == "d00a":
            m_packet = self.make_response_packet(0)
            m_chksum = self.validate_checksum(m_packet, 11)
            if m_chksum[0]:
                self.write(m_packet, self.controller, "controller")
        elif p_prefix == "d08a":
            p_mode = packet[8:12]
            p_speed = packet[12:16]
            fan_speed = GREX_SPEED[p_speed]
            ha_speed = self.status["ventilator"]["speed"]
            mode = GREX_MODE[p_mode]
            speed = {"low": 1, "medium": 2, "high": 3, "off": 0}[fan_speed]
            self.write(self.make_response_packet(speed), self.controller, "controller")
            self.set_cont(fan_speed, mode)

            if ha_speed != "off":
                speed = {"low": 1, "medium": 2, "high": 3, "off": 0}[ha_speed]
                mode = "manual"
            self.set_mode(mode)
            self.write(
                self.make_control_packet(mode, speed), self.ventilator, "ventilator"
            )

        elif p_prefix == "d18b":
            p_speed = packet[8:12]
            self.set_speed(GREX_SPEED[p_speed])

    def make_control_packet(self, mode, speed):
        prefix = "d08ae022"
        if mode == "off":
            packet_mode = "0000"
        elif mode == "auto":
            packet_mode = "0100"
        elif mode == "manual":
            packet_mode = "0200"
        elif mode == "sleep":
            packet_mode = "0300"
        else:
            return ""
        if speed == "off":
            packet_speed = "0000"
        elif speed == "low":
            packet_speed = "0101"
        elif speed == "medium":
            packet_speed = "0202"
        elif speed == "high":
            packet_speed = "0303"
        else:
            return ""
        if ((mode == "auto" or mode == "sleep") and (speed == "off")) or (
            speed == "low" or speed == "medium" or speed == "high"
        ):
            postfix = "0001"
        else:
            postfix = "0000"

        packet = prefix + packet_mode + packet_speed + postfix
        packet_checksum = self.make_checksum(packet, 10)
        packet = packet + packet_checksum
        return packet

    def make_response_packet(self, speed):
        prefix = "d18be021"
        packet_speed = "0000"
        postfix = "0000000000"
        if speed == 0:
            packet_speed = "0000"
        elif speed == 1:
            packet_speed = "0101"
        elif speed == 2:
            packet_speed = "0202"
        elif speed == 3:
            packet_speed = "0303"
        if speed == 0:
            postfix = "0000000000"
        elif speed > 0:
            postfix = "0000000100"

        packet = f"{prefix}{packet_speed}{postfix}"
        packet_checksum = self.make_checksum(packet, 11)
        packet = packet + packet_checksum
        return packet

    def hex_to_list(self, hex_string):
        slide_windows = 2
        start = 0
        buf = []
        for x in range(int(len(hex_string) / 2)):
            buf.append("0x{}".format(hex_string[start:slide_windows].lower()))
            slide_windows += 2
            start += 2
        return buf

    def validate_checksum(self, packet, length):
        hex_list = self.hex_to_list(packet)
        sum_buf = 0
        for ix, x in enumerate(hex_list):
            if ix > 0:
                hex_int = int(x, 16)
                if ix == length:
                    chksum_hex = "0x{0:02x}".format((sum_buf % 256))
                    if hex_list[ix] == chksum_hex:
                        return (True, hex_list[ix])
                    else:
                        return (False, hex_list[ix])
                sum_buf += hex_int

    def make_checksum(self, packet, length):
        hex_list = self.hex_to_list(packet)
        sum_buf = 0
        chksum_hex = 0
        for ix, x in enumerate(hex_list):
            if ix > 0:
                hex_int = int(x, 16)
                sum_buf += hex_int
                if ix == length - 1:
                    chksum_hex = "{0:02x}".format((sum_buf % 256))
        return str(chksum_hex)
