""" Commax API """
import logging
import re
import time
import threading

from homeassistant.components.fan import SPEED_HIGH, SPEED_LOW, SPEED_MEDIUM, SPEED_OFF
from homeassistant.core import callback
from .const import (
    PLATFORMS, WPD_MAIN, WPD_DOORLOCK, WPD_EV, WPD_EVSENSOR, WPD_FAN, WPD_GAS,
    WPD_LIGHT, WPD_MOTION, WPD_SWITCH, WPD_THERMOSTAT, WPD_LIGHTBREAK,
    WPD_MAIN_LIST, FAN_STATE, FAN_OFF, FAN_ON, FAN_SPEED, THERMO_AWAY,
    THERMO_HEAT, THERMO_MODE, THERMO_OFF, THERMO_TARGET, THERMO_TEMP, SIGNAL,
    SEND_INTERVAL, SEND_RETRY, OPT_SEND_RETRY, OPT_SCAN_INT, OPT_SCAN_LIST,
    OPT_SEND_INT, SCAN_INTERVAL, TICK, DEVICE_STATE, DEVICE_INFO,
    DEVICE_UNIQUE, DEVICE_ROOM, DEVICE_GET, DEVICE_SET, DEVICE_REG,
    DEVICE_UNREG, DEVICE_UPDATE, DEVICE_TRY, ENTITY_MAP, DEVICE_ID,
    DEVICE_NAME, DEVICE_TYPE, DEVICE_SUB, CMD_SCAN, CMD_STATUS, CMD_CHANGE,
    CMD_ON, CMD_OFF, CMD_DETECT, CLIMATE_DOMAIN, BINARY_SENSOR_DOMAIN,
    SENSOR_DOMAIN, FAN_DOMAIN, SWITCH_DOMAIN, LIGHT_DOMAIN)
_LOGGER = logging.getLogger(__name__)

COMMAX_PTR = re.compile("(..)(..)(..)(..)(..)....(..)")

BRAND = "COMMAX"
VERSION = "1.2"
SCAN_LIST = []

STATE_LIGHT = ["b0", "b1"]
CMD_LIGHT = "31"  # scan 30
STATE_SWITCH = ["f9", "fa"]
CMD_SWITCH = "7a"  # scan 79
STATE_THERMO = ["82", "84"]
CMD_THERMO = "04"  # scan 02
STATE_GAS = ["90", "91"]
CMD_GAS = "11"  # scan 10
STATE_FAN = ["f6", "f8"]
CMD_FAN = "78"  # scan 76
STATE_LIGHTBREAK = ["a0", "a2"]
CMD_LIGHTBREAK = "22"  # scan 21
STATE_EV = ["23", "22"]
CMD_EV = "a0"
ENTITY_MAP["evsensor"] = SENSOR_DOMAIN

STATE_PACKET = STATE_LIGHT + STATE_SWITCH + STATE_FAN + STATE_THERMO + STATE_GAS + STATE_LIGHTBREAK + STATE_EV
CMD_PACKET = [
    CMD_LIGHT, CMD_SWITCH, CMD_THERMO, CMD_GAS, CMD_FAN, CMD_LIGHTBREAK, CMD_EV
]
PACKET_LEN = 8
STATE_VALUE = {
    "01": True,
    "00": False,
    "11": True,
    "10": False,
    "40": True,
    "80": True,
    "48": False,
    "a0": True,
    "50": False,
    "58": False,
}
CMD_VALUE = {True: "01", False: "00"}

THERMO_MODE_PACKET = {
    "81": THERMO_HEAT,
    "80": THERMO_OFF,
    "01": THERMO_HEAT,
    "00": THERMO_OFF,
    "04": THERMO_HEAT,
    "03": THERMO_HEAT,
}
THERMO = {THERMO_HEAT: "81", THERMO_OFF: "80"}
DEFAULT_TARGET = 22
FAN = {SPEED_OFF: 0, SPEED_LOW: 1, SPEED_MEDIUM: 2, SPEED_HIGH: 3}
FAN_SPEED_LIST = [SPEED_OFF, SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH]
FAN_CMD_ON = "04"


class Main:
    def __init__(self, hass, entry, entities, write, async_add_device):
        _LOGGER.info(f"[{BRAND}] Initialize")
        self.hass = hass
        self.entry = entry
        self.socket_write = write
        self.async_add_device = async_add_device
        self.entities = entities
        self.brand_name = BRAND
        self.brand = BRAND.lower()
        self.version = VERSION
        self.tick = time.time()
        self.packet_que = []
        self.device = {}
        self.unique = {}
        self.fail = {}
        self.avg_tick = 10

        self._que = threading.Thread(target=self.loop)
        self._que.daemon = True
        self._que.start()

        self.thermo_mode = THERMO
        for mode, packet in THERMO.items():
            if self.get_data(mode):
                self.thermo_mode[mode] = packet
        self._packet = []
        self._flag = False

    def set_tick(self):
        self.tick = time.time()

    def get_data(self, name, default=False):
        return self.entry.data.get(name, default)

    def get_option(self, name, default=False):
        return self.entry.options.get(name, default)

    def init_device(self, device_id, sub_id, isInit):
        """
        Init device information.\n
        device_id = device+room\n
        unique_id = device+room+sub_id\n
        self.device[device_id] = {DEVICE_STATE:{sub_id:state}, DEVICE_INFO:{sub_id:{DEVICE_ID,DEVICE_SUB,DEVICE_UNIQUE,DEVICE_NAME}}}\n
        self.unique[unique_id] = {set(),get(),register(),unregister(),update(),id:sub_id,device_type:ENTITY_MAP,unique_id}
        """
        device_type = device_id.split("_")[0]
        device_room = device_id.split("_")[1]
        unique_id = f"{device_id}_{sub_id}"
        device_name = f"{self.brand}_{device_id}"
        if device_id not in self.device:
            self.device[device_id] = {
                TICK: 0 if isInit else time.time() + 5,
                DEVICE_INFO: {},
                DEVICE_STATE: {},
            }
        if sub_id is None: return self.device[device_id]
        if device_type in WPD_MAIN_LIST:
            device_name = f"{self.brand}_{device_type}"
        if sub_id not in self.device[device_id][DEVICE_STATE]:
            self.device[device_id][DEVICE_STATE][sub_id] = None
        if sub_id not in self.device[device_id][DEVICE_INFO]:
            self.device[device_id][DEVICE_INFO][sub_id] = {
                DEVICE_ID: device_id,
                DEVICE_SUB: sub_id,
                DEVICE_ROOM: device_room,
                DEVICE_UNIQUE: unique_id,
                DEVICE_NAME: device_name,
                DEVICE_TYPE: device_type
            }
        if unique_id not in self.unique:
            self.unique[unique_id] = {
                DEVICE_SET: self.set_state,
                DEVICE_GET: self.get_state,
                DEVICE_REG: self.register_update_state,
                DEVICE_UNREG: self.unregister_update_state,
                DEVICE_UPDATE: None,
                DEVICE_SUB: sub_id,
                DEVICE_TYPE: ENTITY_MAP[device_type],
                DEVICE_UNIQUE: unique_id,
                DEVICE_INFO: self.device[device_id][DEVICE_INFO][sub_id],
            }
        return self.unique[unique_id]

    def convert_unique(self, id):
        """ Convert unique_id to device_id, sub_id """
        splt = id.split("_")
        device = splt[0]
        room = splt[1]
        sub = splt[2]
        return f"{device}_{room}", sub

    def convert_entity(self, domain):
        """ Get entity_registry and return device information from entity_id """
        entity_list = self.entities[domain]
        entities = []
        for unique_id in entity_list:
            device_id, sub_id = self.convert_unique(unique_id)
            entities.append(self.init_device(device_id, sub_id, True))
        return entities

    def lights(self):
        """ Init lights from entity_registry """
        return self.convert_entity(LIGHT_DOMAIN)

    def switchs(self):
        """ Init switchs from entity_registry """
        return self.convert_entity(SWITCH_DOMAIN)

    def climates(self):
        """ Init climates from entity_registry """
        return self.convert_entity(CLIMATE_DOMAIN)

    def fans(self):
        """ Init fans from entity_registry """
        return self.convert_entity(FAN_DOMAIN)

    def sensors(self):
        """ Init sensors from entity_registry """
        return self.convert_entity(SENSOR_DOMAIN)

    def binary_sensors(self):
        """ Init binary_sensors from entity_registry """
        return self.convert_entity(BINARY_SENSOR_DOMAIN)

    def write(self, packet):
        """ Send packet and set self.tick """
        if not isinstance(packet, str): return
        self.set_tick()
        self.socket_write(packet)

    def register_update_state(self, unique_id, cb):
        """ Register device update function to update entity state """
        if self.unique[unique_id][DEVICE_UPDATE] is None:
            _LOGGER.debug(f"[{BRAND}] Wallpad register device => {unique_id}")
            self.unique[unique_id][DEVICE_UPDATE] = cb

    def unregister_update_state(self, unique_id):
        """ Unregister device update function """
        if self.unique[unique_id][DEVICE_UPDATE] is not None:
            _LOGGER.debug(
                f"[{BRAND}] Wallpad unregister device => {unique_id}")
            self.unique[unique_id][DEVICE_UPDATE] = None

    def deque(self):
        """ Deque idnex 0 of self.packet_que """
        if len(self.packet_que) > 0:
            self.packet_que.pop(0)

    def queue(self, device_id, sub_id, value):
        """ Insert packet information to queue to send """
        que = {
            TICK: 0,
            DEVICE_TRY: 1,
            DEVICE_ID: device_id,
            DEVICE_SUB: sub_id,
            DEVICE_STATE: value
        }
        self.packet_que.append(que)

    @callback
    def get_state(self, device_id, sub_id):
        """ Get state of entity """
        if device_id in self.device:
            return self.device[device_id][DEVICE_STATE].get(sub_id)

    @callback
    def set_state(self, device_id, sub_id, value):
        """ Set state from entity """
        device_type = device_id.split("_")[0]
        if device_type in [WPD_GAS] and value == False: return
        if device_type in [WPD_EV] and value == False: return
        if device_id in self.device:
            self.queue(device_id, sub_id, value)

    def loop(self):
        """
        Loop to send packet from self.packet_que.\n
        And scan wallpad when init.
        """
        while True:
            if len(self.packet_que) > 0:
                now = time.time()
                que = False
                interval = (self.get_option(OPT_SEND_INT, SEND_INTERVAL) /
                            1000)
                try:
                    que = self.packet_que[0]
                except:
                    continue
                if (que and now - self.tick < self.avg_tick / 1000
                        and now - que[TICK] > interval):
                    count = que[DEVICE_TRY]
                    device_id = que[DEVICE_ID]
                    sub_id = que[DEVICE_SUB]
                    value = que[DEVICE_STATE]
                    packet = self.make_packet(device_id, sub_id, value)
                    retry = self.get_option(OPT_SEND_RETRY, SEND_RETRY)
                    if packet is False: count = retry + 1
                    _LOGGER.debug(
                        f'[{BRAND}] Wallpad packet {"send" if count <= retry else "failed"}{count if count <= retry else ""} => {device_id} > {sub_id} > {value} > {packet}'
                    )
                    if count > retry:
                        if device_id not in self.fail:
                            self.fail[device_id] = 0
                        self.fail[device_id] += 1
                        self.device[device_id][TICK] = time.time()
                        self.deque()
                    else:
                        que[TICK] = now
                        que[DEVICE_TRY] += 1
                        self.write(packet)
            else:
                now = time.time()
                dev = self.device.copy()
                for device_id, device in dev.items():
                    device_type = device_id.split("_")[0]
                    if (now - device[TICK] > self.get_option(
                            OPT_SCAN_INT, SCAN_INTERVAL)
                            and device_type in self.get_option(
                                OPT_SCAN_LIST, SCAN_LIST)):
                        self.device[device_id][TICK] = now
                        self.queue(device_id, None, CMD_SCAN)

    def set_device(self, device_id, state, packet):
        """
        Set device state from wallpad.\n
        device_id = device+room / state = list|dict
        """
        device_type = device_id.split("_")[0]
        wpd_to_entity = ENTITY_MAP[device_type]
        add_device = SIGNAL[wpd_to_entity]
        if device_id in self.fail: self.fail[device_id] = 0

        def add(did, sid, value):
            if did is None: return
            device_info = self.init_device(did, sid, False)
            if value == True or sid.isalpha():
                self.async_add_device(add_device, device_info)

        def update(did, sid, old, new):
            if did is None: return
            unique_id = f"{did}_{sid}"
            if (self.unique.get(unique_id) and old.get(sid) != new):
                update = self.unique[unique_id][DEVICE_UPDATE]
                if update is not None: update()

        if len(self.packet_que) > 0:
            que = self.packet_que[0]
            copy = state[DEVICE_STATE].copy() if isinstance(
                state[DEVICE_STATE], dict) else state[DEVICE_STATE]
            if isinstance(state[DEVICE_STATE], dict) and copy.get(
                    THERMO_TEMP, False):
                copy.pop(THERMO_TEMP)
            if que[DEVICE_ID] == device_id and que[DEVICE_STATE] == copy:
                self.deque()
        if wpd_to_entity in PLATFORMS:
            for sub_id, value in state.items():
                add(device_id, sub_id, value)
        else:
            _LOGGER.info(
                f"[{BRAND}] Wallpad unknown device {device_id} => {state[DEVICE_STATE]} > {packet}"
            )

        if device_id not in self.device: return
        self.device[device_id][TICK] = time.time()
        old_state = self.device[device_id][DEVICE_STATE]
        if old_state != state:
            _LOGGER.debug(
                f"[{BRAND}] Wallpad {device_id} => {state[DEVICE_STATE]} > {packet}"
            )
            if wpd_to_entity in PLATFORMS:
                self.device[device_id][DEVICE_STATE] = state
                for sub_id, value in state.items():
                    update(device_id, sub_id, old_state, value)

    def checksum(self, packet):
        """ Validate checksum > (sum)%256 """
        if len(packet) < 7:
            return False
        p_sum = 0
        for i in range(0, 7):
            p_sum += int(packet[i], 16)
        c_sum = '{0:02x}'.format((p_sum) % 256)
        return packet[7] == c_sum

    def makesum(self, packet):
        """ Make checksum > (sum)%256 """
        if len(packet) < 7:
            return False
        p_sum = 0
        for i in range(0, 7):
            p_sum += int(packet[i], 16)
        c_sum = '{0:02x}'.format((p_sum) % 256)
        return c_sum

    def make_packet(self, device_id, sub_id, value):
        """ Make packet from device_id, sub_id, value """
        splt = device_id.split("_")
        device = splt[0]
        room = splt[1]
        packet_str = None

        def make_light():
            """ Make value packet of light """
            return f"{CMD_LIGHT}{room}{CMD_VALUE[value]}00000000"

        def make_switch():
            """ Make packet of switch """
            return f"{CMD_SWITCH}{room}01{CMD_VALUE[value]}000000"

        def make_thermostat():
            """ Make packet of thermostat """
            state = self.get_state(device_id, sub_id)
            cmd, target = None, None
            if value[THERMO_MODE] == THERMO_OFF:
                cmd = "04"
                target = self.thermo_mode[value[THERMO_MODE]]
            else:
                cmd = "04" if state[THERMO_MODE] == THERMO_OFF else "03"
                target = self.thermo_mode[
                    value[THERMO_MODE]] if cmd == "04" else int(
                        value[THERMO_TARGET])
            return f"{CMD_THERMO}{room}{cmd}{target}000000"

        def make_fan():
            """ Make packet of fan """
            state = self.get_state(device_id, sub_id)
            cmd, target = None, None
            if value[DEVICE_STATE] == FAN_ON:
                cmd = "01" if state[DEVICE_STATE] == FAN_OFF else "02"
                target = "04" if state[
                    DEVICE_STATE] == FAN_OFF else "{0:02x}".format(
                        FAN[value[FAN_SPEED]])
            else:
                cmd = "01"
                target = "00"
            return f"{CMD_FAN}{room}{cmd}{target}000000"

        def make_gas():
            """ Make packet of gas """
            return "11018000000000"

        def make_ev():
            """ Make packet of ev """
            return "a0010100081500"

        def make_lightbreak():
            """ Make packet of ev """
            if value:
                return "22010001000000"
            else:
                return "22010101000000"

        if device == WPD_LIGHT:
            packet_str = make_light()
        elif device == WPD_SWITCH:
            packet_str = make_switch()
        elif device == WPD_THERMOSTAT:
            packet_str = make_thermostat()
        elif device == WPD_FAN:
            packet_str = make_fan()
        elif device == WPD_GAS:
            packet_str = make_gas()
        elif device == WPD_EV:
            packet_str = make_ev()
        elif device == WPD_LIGHTBREAK:
            packet_str = make_lightbreak()

        if packet_str is None: return False
        try:
            packet = [
                packet_str[i:i + 2] for i in range(0, len(packet_str), 2)
            ]
            chksum = self.makesum(packet)
            packet.append(chksum)
            if not self.checksum(packet): return False
            return "".join(packet)
        except:
            _LOGGER.debug(
                f"[{BRAND}] Wallpad make failed => {device_id} > {sub_id} > {value}"
            )
            return False

    def parse(self, packet):
        """ Parse packet """
        packet = "".join(packet)
        pmatch = COMMAX_PTR.match(packet)
        p = [
            pmatch.group(1),
            pmatch.group(2),
            pmatch.group(3),
            pmatch.group(4),
            pmatch.group(5),
            pmatch.group(6)
        ]
        device = p[0]
        device_id, state = None, None

        def parse_light(p1, p2):
            """ Parse light """
            device_id = f"{WPD_LIGHT}_{p2}"
            return device_id, STATE_VALUE[p1]

        def parse_switch(p1, p2):
            """ Parse switch """
            device_id = f"{WPD_SWITCH}_{p2}"
            return device_id, STATE_VALUE[p1]

        def parse_thermostat(p1, p2, p3, p4):
            """ Parse thermostat """
            device_id = f"{WPD_THERMOSTAT}_{p2}"
            mode = THERMO_MODE_PACKET[p1]
            status = {
                THERMO_MODE: mode,
                THERMO_TEMP: int(p3),
                THERMO_TARGET: int(p4)
            }
            return device_id, status

        def detect_thermostat(p2, p3):
            """ Detect thermostat mode """
            if p2 != "04": return
            mode = THERMO_MODE_PACKET[p3]
            if self.thermo_mode[mode] != p3:
                self.thermo_mode[mode] = p3
                self.hass.config_entries.async_update_entry(
                    entry=self.entry, data={
                        **self.entry.data, mode: p3
                    })

        def parse_fan(p1, p2, p3):
            """ Parse fan """
            device_id = f"{WPD_FAN}_{p2}"
            speed = FAN_SPEED_LIST[int(p3, 16)]
            status = {
                FAN_STATE: FAN_ON if speed != SPEED_OFF else FAN_OFF,
                FAN_SPEED: speed,
            }
            return device_id, status

        def parse_gas(p1):
            """ Parse gas """
            device_id = f"{WPD_GAS}_01"
            return device_id, not STATE_VALUE[p1]

        def parse_lightbreak(p1, p2):
            """ Parse lightbreak """
            device_id = f"{WPD_LIGHTBREAK}_{p2}"
            return device_id, not STATE_VALUE[p1]

        def parse_ev_onoff(packet):
            """ Parse ev """
            device_id = f"{WPD_EV}_01"
            return device_id, packet == "220140070000006a"

        def parse_ev_floor(p1, p2):
            """ Parse ev """
            device_id = f"{WPD_EVSENSOR}_{p1}"
            return device_id, int(p2, 16)

        try:
            if device in STATE_PACKET:
                self.set_tick()
            if device in STATE_GAS:
                device_id, state = parse_gas(p[1])
            elif device in STATE_SWITCH:
                device_id, state = parse_switch(p[1], p[2])
            elif device in STATE_LIGHT:
                device_id, state = parse_light(p[1], p[2])
            elif device in STATE_FAN:
                device_id, state = parse_fan(p[1], p[2], p[3])
            elif device in STATE_THERMO:
                device_id, state = parse_thermostat(p[1], p[2], p[3], p[4])
            elif device in STATE_LIGHTBREAK:
                device_id, state = parse_lightbreak(p[1], p[2])
            elif device in STATE_EV:
                if device == "22":
                    device_id, state = parse_ev_onoff(packet)
                elif device == "23":
                    device_id, state = parse_ev_floor(p[1], p[2])
            elif device in [
                    CMD_GAS, CMD_SWITCH, CMD_LIGHT, CMD_FAN, CMD_THERMO,
                    CMD_LIGHTBREAK, CMD_EV
            ]:
                if device == CMD_THERMO:
                    detect_thermostat(p[2], p[3])
                _LOGGER.debug(
                    f"[{BRAND}] Wallpad packet command {device} -> {packet}")
        except:
            _LOGGER.info(f"[{BRAND}] Wallpad parse error -> {packet}")

        if device_id is not None:
            self.set_device(device_id, {DEVICE_STATE: state}, packet)

    def poll(self, p):
        """ Get packet from tcp/ip socket and validate checksum. """
        if p is not None and isinstance(p, str) and p != "":
            self._packet.append(p)
            if "".join(self._packet).find("1001000000000011") != -1:
                self._packet.clear()
                self._flag = True
            if len(self._packet) >= PACKET_LEN and self._flag:
                if self.checksum(self._packet):
                    self.parse(self._packet)
                    self._packet.clear()
