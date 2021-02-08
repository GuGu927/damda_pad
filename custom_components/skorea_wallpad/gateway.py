import socket
import serial
import threading
import logging
import time
import re

from .api_kocom import Main as Kocom
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (CONF_SOCKET, CONF_PORT, CONF_WPD, NAME, DOMAIN, BRAND,
                    VERSION, MODEL, NEW_LIGHT, NEW_SWITCH, NEW_FAN,
                    NEW_CLIMATE, NEW_SENSOR, NEW_BSENSOR, RELOAD_SIGNAL,
                    CLIMATE_DOMAIN, BINARY_SENSOR_DOMAIN, SENSOR_DOMAIN,
                    FAN_DOMAIN, SWITCH_DOMAIN, LIGHT_DOMAIN)

_LOGGER = logging.getLogger(__name__)
ip_regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"


def rs_type(v):
    if (re.search(ip_regex, v)):
        return "socket"
    else:
        return "serial"


@callback
def get_wallpad(hass, entry):
    """Return gateway with a matching socket ip."""
    return hass.data[DOMAIN][entry.unique_id]


class WallpadGateway:
    def __init__(
        self,
        hass=None,
        entry=None,
    ):
        """Initialize the WallpadGateway"""
        _LOGGER.info(f"[{BRAND}] Initialize Wallpad")
        self.hass = hass
        self.entry = entry
        self.dr_id = None

        self._rs485 = {"type": rs_type(self.host), "connect": None}
        self._poll = False
        self.api = None

        self.unload_gateway = False
        self.reload = False
        self.available = False

        self.entities = {
            CLIMATE_DOMAIN: set(),
            BINARY_SENSOR_DOMAIN: set(),
            SENSOR_DOMAIN: set(),
            SWITCH_DOMAIN: set(),
            LIGHT_DOMAIN: set(),
            FAN_DOMAIN: set()
        }
        self.listeners = []

    @property
    def rs_type(self) -> str:
        """Return the socket ip address."""
        return self._rs485["type"]

    @property
    def host(self) -> str:
        """Return the connection type(IP addr or USB dir)"""
        return self.entry.data.get(CONF_SOCKET)

    @property
    def port(self) -> int:
        """Return the socket port."""
        return self.entry.data.get(CONF_PORT)

    @property
    def manufacturer(self) -> str:
        """Return the registered wallpad."""
        return self.entry.data.get(CONF_WPD)

    @property
    def version(self) -> str:
        return VERSION

    @property
    def device_id(self):
        return self.dr_id

    @property
    def brand(self) -> str:
        return BRAND

    @property
    def name(self) -> str:
        return NAME

    @property
    def model(self) -> str:
        return f"{MODEL}_{VERSION}"

    async def async_get_entity_registry(self) -> None:
        entity_registry = await self.hass.helpers.entity_registry.async_get_registry(
        )
        get_entities = self.hass.helpers.entity_registry.async_entries_for_config_entry(
            entity_registry, self.entry.entry_id)
        for entity in get_entities:
            splt = entity.entity_id.split(".")
            domain = splt[0]
            if entity.unique_id not in self.entities[domain]:
                self.entities[domain].add(entity.unique_id)

    async def async_update_device_registry(self) -> None:
        """Update device registry."""
        device_registry = await self.hass.helpers.device_registry.async_get_registry(
        )

        device = device_registry.async_get_or_create(
            config_entry_id=self.entry.entry_id,
            connections={(DOMAIN, self.host)},
            identifiers={(DOMAIN, self.host)},
            manufacturer=self.brand,
            name=self.name,
            model=self.model,
            sw_version=self.version,
            via_device=(DOMAIN, self.host),
        )
        self.dr_id = device.id

    @callback
    def async_signal_new_device(self, device_type) -> str:
        """Wallpad specific event to signal new device."""
        new_device = {
            NEW_FAN: f"wallpad_new_fan_{self.manufacturer}",
            NEW_CLIMATE: f"wallpad_new_climate_{self.manufacturer}",
            NEW_LIGHT: f"wallpad_new_light_{self.manufacturer}",
            NEW_SWITCH: f"wallpad_new_switch_{self.manufacturer}",
            NEW_SENSOR: f"wallpad_new_sensor_{self.manufacturer}",
            NEW_BSENSOR: f"wallpad_new_binary_sensor_{self.manufacturer}",
        }
        return new_device[device_type]

    @callback
    def async_add_device_callback(self,
                                  device_type,
                                  device=None,
                                  force: bool = False) -> None:
        """Handle event of new device creation in Wallpad."""

        args = []
        if device["unique_id"] in self.entities[device["device_type"]]: return

        if device is not None and not isinstance(device, list):
            args.append([device])

        async_dispatcher_send(self.hass,
                              self.async_signal_new_device(device_type), *args)

    def initialize(self):
        if self._rs485["connect"]:
            self.available = True
            if self.manufacturer is None:
                self._poll = True
                self._polling = threading.Thread(target=self.get_socket)
                self._polling.daemon = True
                self._polling.start()
            else:
                self.set_wallpad(self.manufacturer, False)

    def connect(self):
        if self.unload_gateway: return
        if self.available:
            self._rs485["connect"].close()
        self.available = False
        if self._rs485["type"] == "socket":
            soc = socket.socket()
            soc.setblocking(False)
            soc.settimeout(10)
            try:
                soc.connect((self.host, int(self.port)))
            except Exception as e:
                _LOGGER.info(
                    f"[{BRAND}] {self._rs485['type']} 에 연결할 수 없습니다.[{self.host}:{self.port}][{e}]"
                )
                return False
            soc.settimeout(240)
            self._rs485["connect"] = soc
        elif self._rs485["connect"] == "serial":
            try:
                ser = serial.Serial(self.host, 9600, timeout=None)
                if ser.isOpen():
                    ser.bytesize = 8
                    ser.stopbits = 1
                    ser.parity = serial.PARITY_NONE if self.manufacturer != "samsungsds" else serial.PARITY_EVEN
                    self._rs485["connect"] = ser
            except Exception as e:
                _LOGGER.info(
                    f"[{BRAND}] {self._rs485['type']} 에 연결할 수 없습니다.[{self.host}][{e}]"
                )
                return False
        if self._rs485["connect"] is not None:
            self.available = True
            _LOGGER.info(
                f"[{BRAND}] {self._rs485['type']} 에 연결했습니다. {self.host}:{self.port}"
            )
            return True
        return False

    def retry(self):
        if self.unload_gateway: return
        _LOGGER.info(f"[{BRAND}] {self._rs485['type']} 에러. 재시작합니다.")
        if not self.connect():
            time.sleep(60)
            self.retry()

    @callback
    def stop(self, event) -> None:
        if self._rs485["connect"]:
            _LOGGER.info(f"[{BRAND}] {self._rs485['type']} 종료.")
            self.unload_gateway = True
            self.available = False
            self._rs485["connect"].close()
            self._rs485["connect"] = None

    @callback
    def write(self, packet):
        if self.unload_gateway: return
        if self.available:
            try:
                if self._rs485['type'] == "serial":
                    self._rs485["connect"].write(bytearray.fromhex(packet))
                else:
                    self._rs485["connect"].send(bytearray.fromhex(packet))
            except socket.timeout:
                self.connect()
            except Exception as e:
                _LOGGER.info(f"[{BRAND}] {self._rs485['type']} 에러 write {e}")
                self.retry()

    def read(self):
        if self.unload_gateway: return
        if self.available:
            try:
                if self._rs485['type'] == "serial":
                    return self._rs485["connect"].read(
                    ) if self._rs485["connect"].readable() else ""
                else:
                    return self._rs485["connect"].recv(1)
            except socket.timeout:
                self.connect()
            except Exception as e:
                _LOGGER.info(f"[{BRAND}] {self._rs485['type']} 에러 read {e}")
                self.retry()

    def set_wallpad(self, wallpad=None, config=False):
        if wallpad == "kocom":
            self.api = Kocom(self.hass, self.entry, self.entities, self.write,
                             self.async_add_device_callback)
        elif wallpad == "commax":
            self.api = Commax(self.hass, self.entry, self.entities, self.write,
                              self.async_add_device_callback)
        if self._poll == False:
            self._poll = True
            self._polling = threading.Thread(target=self.get_socket)
            self._polling.daemon = True
            self._polling.start()
        if self.api is not None:
            _LOGGER.info(f"[{BRAND}] 월패드 로딩완료 => {wallpad}")
            if config:
                self.hass.config_entries.async_update_entry(
                    entry=self.entry,
                    title=self.host,
                    data={
                        **self.entry.data, CONF_WPD: wallpad
                    })
                self.reload = True

    def get_socket(self):
        while (True and self.unload_gateway is False and self.reload is False):
            if self.available:
                if self.manufacturer is None:
                    self.finding()
                elif self.api is not None:
                    self.poll()
        if self.reload:
            async_dispatcher_send(self.hass, RELOAD_SIGNAL, self.hass,
                                  self.entry)
        else:
            self.get_socket()

    def finding(self):
        target = ""
        buf = []
        start_flag = False
        finding = ["aa", "f7", "b0", "90", "ac", "ae", "ad"]
        kocom = ["aa55"]
        cvnet = ["f720"]
        ezville = ["f70e", "f736", "f732", "f73a", "f733"]
        commax = [
            "b000", "b001", "8280", "8281", "8284", "f600", "f602", "f604",
            "f606", "9048", "9040", "9080", "9050", "90a0", "f900", "f901",
            "f990", "f991"
        ]
        samsungsds = [
            "ac79", "b079", "ae7c", "b07c", "c24e", "b04e", "ad41", "b041"
        ]
        imazu = ["f70d", "f70b", "f70c", "f722", "f70e"]
        bestin = []
        while target == "":
            row_data = self.read()
            if row_data is not None:
                hex_d = row_data.hex()
                if hex_d in finding:
                    start_flag = True
                if start_flag == True:
                    buf.append(hex_d)
                if len(buf) >= 2:
                    joindata = "".join(buf)
                    if joindata in kocom:
                        target = "kocom"
                    elif joindata in ezville:
                        target = "ezville"
                    elif joindata in cvnet:
                        target = "cvnet"
                    elif joindata in commax:
                        target = "commax"
                    elif joindata in samsungsds:
                        target = "samsungsds"
                    elif joindata in imazu:
                        target = "imazu"
                    buf = []
                    start_flag = False
        if target != "":
            self.set_wallpad(target, True)

    def poll(self):
        row_data = self.read()
        if row_data is not None:
            hex_d = row_data.hex()
            self.api.poll(hex_d)