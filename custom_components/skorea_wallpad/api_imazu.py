""" Imazu API """
import logging
import re
import time
import threading

from homeassistant.components.fan import SPEED_HIGH, SPEED_LOW, SPEED_MEDIUM, SPEED_OFF
from homeassistant.core import callback
from .const import (
    DOMAIN, CONN_STATUS, PLATFORMS, WPD_MAIN, WPD_DOORLOCK, WPD_EV,
    WPD_EVSENSOR, WPD_FAN, WPD_GAS, WPD_LIGHT, WPD_POWER, WPD_MOTION,
    WPD_SWITCH, WPD_THERMOSTAT, WPD_LIGHTBREAK, WPD_AWAYMODE, WPD_GUARD,
    WPD_USAGE, WPD_MAIN_LIST, FAN_STATE, FAN_OFF, FAN_ON, FAN_SPEED,
    THERMO_AWAY, THERMO_HEAT, THERMO_MODE, THERMO_OFF, THERMO_TARGET,
    THERMO_TEMP, SIGNAL, SEND_INTERVAL, SEND_RETRY, OPT_SEND_RETRY,
    OPT_SCAN_INT, OPT_SCAN_LIST, OPT_SEND_INT, SCAN_LIST, SCAN_INTERVAL, TICK,
    DEVICE_STATE, DEVICE_INFO, DEVICE_UNIQUE, DEVICE_ROOM, DEVICE_GET,
    DEVICE_SET, DEVICE_REG, DEVICE_UNREG, DEVICE_UPDATE, DEVICE_TRY,
    ENTITY_MAP, DEVICE_ID, DEVICE_NAME, DEVICE_TYPE, DEVICE_SUB, CMD_SCAN,
    CMD_STATUS, CMD_CHANGE, CMD_ON, CMD_OFF, CMD_DETECT, CLIMATE_DOMAIN,
    BINARY_SENSOR_DOMAIN, SENSOR_DOMAIN, FAN_DOMAIN, SWITCH_DOMAIN,
    LIGHT_DOMAIN)
_LOGGER = logging.getLogger(__name__)

IMAZU_PTR = re.compile("f7(..)(..)(..)(..)(..)(..)(..)(.*)(..)ee")

BRAND = "IMAZU"
VERSION = "1.0"

IGNORE = "ingore"
WPD_DEVICE = {
    "19": WPD_LIGHT,
    "1f": WPD_SWITCH,
    "18": WPD_THERMOSTAT,
    "1b": WPD_GAS,
    "2b": WPD_FAN,
    "2a": WPD_AWAYMODE,
    "34": WPD_EV,
    "16": WPD_GUARD,
    "4b": IGNORE,
    "43": WPD_USAGE,
}
DEVICE_PACKET = {value: key for key, value in WPD_DEVICE.items()}

USAGE_DEVICE = {"11": "consumption", "13": "gas", "14": "water"}
USAGE_PACKET = {value: key for key, value in USAGE_DEVICE.items()}

CMD = {"01": CMD_SCAN, "02": CMD_CHANGE, "04": CMD_STATUS}
CMD_PACKET = {value: key for key, value in CMD.items()}
CMD_BOOL = "40"
CMD_VALVE = "43"
CMD_MODE = "46"
CMD_TEMP = "45"
CMD_SPPED = "44"
CMD_EV = "41"

THERMO = {THERMO_HEAT: "01", THERMO_OFF: "04", THERMO_AWAY: "07"}
THERMO_MODE_PACKET = {value: key for key, value in THERMO.items()}
DEFAULT_TARGET = 22
FAN = {
    SPEED_LOW: "01",
    SPEED_MEDIUM: "03",
    SPEED_HIGH: "07",
}
FAN_PARSE = {value: key for key, value in FAN.items()}
BOOL_ON = "01"
BOOL_OFF = "02"
GAS_OPEN = "04"
GAS_CLOSE = "03"
GUARD_ON = "07"
GUARD_OFF = "08"
AWAY_VALUE = {
    "01": True,
    "02": False,
    "00": False,
    "03": True,
    "04": False,
    "80": False,
    "07": True,
    "08": False
}
FAN_SPEED_LIST = [SPEED_OFF, SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH]
EV_SENSOR = {"01": "도착", "a6": "UP", "b6": "DOWN"}

PACKET_HEADER = "f7"
PACKET_TAIL = "ee"


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
        self._que = threading.Thread(target=self.loop)
        self._que.daemon = True
        self._que.start()

        self.ev_call = 0
        self.ev_reg = False
        self.grab = []
        self.thermo_type = self.get_data("thermo_type", "01")
        self.thermo_mode = THERMO
        for mode, packet in THERMO.items():
            if self.get_data(mode):
                self.thermo_mode[mode] = packet
        self._packet = []
        self._flag = False

    @property
    def available(self):
        return self.hass.data[DOMAIN][CONN_STATUS]

    def set_tick(self, offset=0):
        self.tick = time.time() + offset

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
        device_name = f"{self.brand}_{device_id}_{sub_id}"
        if device_id not in self.device:
            self.device[device_id] = {
                TICK: time.time() + 5,
                DEVICE_INFO: {},
                DEVICE_STATE: {},
            }
        if sub_id is None: return self.device[device_id]
        if device_type in WPD_MAIN_LIST:
            device_name = f"{self.brand}_{device_type}"
        if device_type in [WPD_THERMOSTAT]:
            device_name = f"{self.brand}_{device_id}"
        if device_type in [WPD_AWAYMODE]:
            device_name = f"{self.brand}_{device_type}_{device_room}"
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
        if device_type in [WPD_GAS, WPD_EV] and value == False: return
        if device_type == WPD_EV:
            self.set_device(device_id, {DEVICE_STATE: True}, "EV call from HA")
            return
        if device_id in self.device:
            self.queue(device_id, str(sub_id), value)

    def loop(self):
        """
        Loop to send packet from self.packet_que.\n
        And scan wallpad when init.
        """
        while True:
            if len(self.packet_que) > 0 and self.available:
                now = time.time()
                que = False
                try:
                    que = self.packet_que[0]
                except:
                    continue
                interval = self.get_option(OPT_SEND_INT, SEND_INTERVAL) / 1000
                value = que[DEVICE_STATE]
                if value == CMD_SCAN: interval = interval * 3
                if (que and now - self.tick > interval
                        and now - que[TICK] > interval):
                    count = que[DEVICE_TRY]
                    device_id = que[DEVICE_ID]
                    sub_id = que[DEVICE_SUB]
                    packet = self.make_packet(device_id, sub_id, value)
                    retry = self.get_option(OPT_SEND_RETRY, SEND_RETRY)
                    if packet is False: count = retry + 1
                    _LOGGER.debug(
                        f'[{BRAND}] Wallpad packet {"send" if count <= retry else "failed"}{count if count <= retry else ""} => {device_id} > {sub_id} > {value} > {packet}'
                    )
                    if count > retry:
                        self.device[device_id][TICK] = now
                        self.deque()
                    else:
                        que[TICK] = now
                        que[DEVICE_TRY] += 1
                        self.write(packet)
            elif self.available:
                now = time.time()
                dev = self.device.copy()
                for device_id, device in dev.items():
                    device_type = device_id.split("_")[0]
                    device_room = device_id.split("_")[1]
                    isScan = False
                    if device_type in [WPD_THERMOSTAT]:
                        if device_room == "0": isScan = True
                    else:
                        isScan = True
                    if isScan:
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
        device_room = device_id.split("_")[1]
        wpd_to_entity = ENTITY_MAP[
            device_type] if device_type != WPD_AWAYMODE else BINARY_SENSOR_DOMAIN
        add_device = SIGNAL[wpd_to_entity]

        def add(did, sid, value):
            if did is None: return
            device_info = self.init_device(did, sid, False)
            self.async_add_device(add_device, device_info)

        def update(did, sid, old, new):
            if did is None: return
            unique_id = f"{did}_{sid}"
            if (self.unique.get(unique_id, None)
                    and old.get(sid, None) != new):
                update = self.unique[unique_id][DEVICE_UPDATE]
                if update is not None: update()

        if len(self.packet_que) > 0:
            que = self.packet_que[0]
            right_id = que[DEVICE_ID] == device_id
            is_scan = que[DEVICE_STATE] == CMD_SCAN
            is_target = False
            if not is_scan and right_id:
                if device_type == WPD_THERMOSTAT:
                    is_mode = que[DEVICE_STATE][THERMO_MODE] == state.get(
                        que[DEVICE_SUB], {}).get(THERMO_MODE, None)
                    is_temp = que[DEVICE_STATE][THERMO_TARGET] == state.get(
                        que[DEVICE_SUB], {}).get(THERMO_TARGET, None)
                    is_target = is_mode and is_temp
                elif device_type == WPD_FAN:
                    mode = state.get(que[DEVICE_SUB], {}).get(FAN_STATE, None)
                    speed = state.get(que[DEVICE_SUB], {}).get(FAN_SPEED, None)
                    is_mode = que[DEVICE_STATE][FAN_STATE] == mode
                    is_speed = que[DEVICE_STATE][FAN_SPEED] == speed
                    is_target = (is_mode
                                 and is_speed) if mode == FAN_ON else is_mode
                else:
                    is_target = que[DEVICE_STATE] == state.get(
                        que[DEVICE_SUB], None)
            if (right_id and (is_scan or is_target)):
                self.deque()
        if wpd_to_entity in PLATFORMS:
            if device_type == WPD_THERMOSTAT and device_room == "0":
                self.init_device(device_id, DEVICE_STATE, False)
                for room_id, sub_value in state.items():
                    d_id = f"{device_type}_{room_id}"
                    self.set_device(d_id, sub_value, packet)
            elif device_type == WPD_AWAYMODE and device_room == "0":
                self.init_device(device_id, DEVICE_STATE, False)
                for room_id, sub_value in state[DEVICE_STATE].items():
                    d_id = f"{device_type}_{room_id}"
                    self.set_device(d_id, {DEVICE_STATE: sub_value}, packet)
                return
            elif device_type == WPD_EV and device_room == "0":
                for room_id, sub_value in state[DEVICE_STATE].items():
                    d_id = f"{room_id}_1"
                    self.set_device(d_id, {DEVICE_STATE: sub_value}, packet)
                return
            else:
                for sub_id, value in state.items():
                    add(device_id, sub_id, value)
        else:
            _LOGGER.info(
                f"[{BRAND}] Wallpad unknown device {device_id} => {state} -> {packet}"
            )

        if device_id not in self.device: return

        self.device[device_id][TICK] = time.time()
        if device_type == WPD_THERMOSTAT and device_room == "0": return
        old_state = self.device[device_id][DEVICE_STATE]
        if device_type == WPD_AWAYMODE:
            old_light = old_state.get(WPD_LIGHT, None)
            if old_light is not None and state.get(WPD_LIGHT) == None:
                state[WPD_LIGHT] = old_light
        if len(old_state) > len(state):
            for k, v in old_state.items():
                if state.get(k, None) is None:
                    state[k] = v
        if old_state != state:
            _LOGGER.debug(
                f"[{BRAND}] Wallpad {device_id} => {state} -> {packet}")
            if wpd_to_entity in PLATFORMS:
                self.device[device_id][DEVICE_STATE] = state
                for sub_id, value in state.items():
                    update(device_id, sub_id, old_state, value)

    def checksum(self, packet):
        """ Validate checksum > xor """
        if len(packet) == 0 or len(packet) != int(packet[1], 16): return False
        p_sum = 0
        for i in range(0, len(packet) - 2):
            p_sum ^= int(packet[i], 16)
        c_sum = '{0:02x}'.format(p_sum)
        return packet[len(packet) - 2] == c_sum

    def makesum(self, packet):
        """ Make checksum > xor """
        if len(packet) < int(packet[1], 16) - 2:
            return False
        p_sum = 0
        for i in range(0, len(packet)):
            p_sum ^= int(packet[i], 16)
        c_sum = '{0:02x}'.format(p_sum)
        return c_sum

    def make_packet(self, device_id, sub_id, value):
        """ Make packet from device_id, sub_id, value """
        splt = device_id.split("_")
        device = splt[0]
        room = splt[1]
        sub_id = "0" if sub_id is None or value == CMD_SCAN else sub_id
        packet = ["f7"]
        packet.append("1a" if device == WPD_THERMOSTAT
                      and self.thermo_type == "1a" else "01")
        packet.append(DEVICE_PACKET[device])
        packet.append(CMD_PACKET[CMD_CHANGE]
                      if value != CMD_SCAN else CMD_PACKET[CMD_SCAN])

        def make_light():
            """ Make value packet of light """
            packet.append(CMD_BOOL)
            packet.append(f"{room}{sub_id}")
            packet.append(BOOL_ON if value else BOOL_OFF)
            packet.append("00")

        def make_switch():
            """ Make packet of switch """
            packet.append(CMD_BOOL)
            packet.append(f"{room}{sub_id}")
            packet.append(BOOL_ON if value else BOOL_OFF)
            packet.append("00")

        def make_thermostat():
            """ Make packet of thermostat """
            state = self.get_state(device_id, DEVICE_STATE)
            cmd, target = None, None
            if value == CMD_SCAN:
                cmd = CMD_MODE
                target = "00"
            else:
                if value[THERMO_MODE] == THERMO_OFF:
                    cmd = CMD_MODE
                    target = self.thermo_mode[value[THERMO_MODE]]
                else:
                    cmd = CMD_MODE if state[
                        THERMO_MODE] == THERMO_OFF else CMD_TEMP
                    target = self.thermo_mode[value[
                        THERMO_MODE]] if cmd == CMD_MODE else "{0:02x}".format(
                            int(float(value[THERMO_TARGET])))
            packet.append(cmd)
            packet.append(f"1{room}")
            packet.append(target)
            packet.append("00")

        def make_fan():
            """ Make packet of fan """
            state = self.get_state(device_id, sub_id)
            cmd, target = None, None
            if value[DEVICE_STATE] == FAN_ON:
                cmd = "40" if state[DEVICE_STATE] == FAN_OFF else "42"
                target = BOOL_ON if state[DEVICE_STATE] == FAN_OFF else FAN[
                    value[FAN_SPEED]]
            else:
                cmd = "40"
                target = BOOL_OFF
            packet.append(cmd)
            packet.append("11")
            packet.append(target)
            packet.append("00")

        def make_gas():
            """ Make packet of gas """
            packet.append(CMD_VALVE)
            packet.append("11")
            packet.append(GAS_CLOSE)
            packet.append("00")

        def make_awaymode():
            """ Make packet of awaymode """
            return "a0010100081500bf"

        def make_usage():
            """ Make packet of usages """
            packet.append(USAGE_PACKET[room])
            packet.append("11")
            packet.append("00")
            packet.append("00")

        if device == WPD_LIGHT:
            make_light()
        elif device == WPD_SWITCH:
            make_switch()
        elif device == WPD_THERMOSTAT:
            make_thermostat()
        elif device == WPD_FAN:
            make_fan()
        elif device == WPD_GAS:
            make_gas()
        elif device == WPD_AWAYMODE:
            make_awaymode()
            return False
        elif device == WPD_USAGE:
            make_usage()

        packet.insert(1, "{:02x}".format(len(packet) + 3))
        chksum = self.makesum(packet)
        packet.append(chksum)
        packet.append("ee")
        if not self.checksum(packet): return False
        return "".join(packet)

    def parse(self, packet):
        """ Parse packet """
        packet = "".join(packet)
        pmatch = IMAZU_PTR.match(packet)
        p = [
            pmatch.group(1),  #0 len
            pmatch.group(2),  #1 01 or 1a(thermo)
            pmatch.group(3),  #2 device
            pmatch.group(4),  #3 cmd
            pmatch.group(5),  #4 state
            pmatch.group(6),  #5 sub
            pmatch.group(7),  #6 send
            pmatch.group(8),  #7 data
            pmatch.group(9),  #8 checksum
        ]
        device = WPD_DEVICE.get(p[2], p[2])
        cmd = CMD.get(p[3], p[3])
        cmd_state = p[4]
        room = int(p[5][:1], 16)
        sub_id = int(p[5][1:2], 16)
        cvalue = p[6]
        pvalue = p[7]
        device_id, value = None, None

        def parse_light():
            """ Parse light """
            id = f"{device}_{room}"
            if sub_id == 0:
                state = [
                    pvalue[i:i + 2] == BOOL_ON
                    for i in range(0, len(pvalue), 2)
                ]
                status = {}
                for i, v in enumerate(state):
                    status[str(i + 1)] = v
                return id, status
            else:
                return id, {str(sub_id): pvalue == BOOL_ON}

        def detect_light():
            """ Detect light command from wallpad """
            id = f"{device}_{room}"
            if sub_id == 0:
                status = {}
                for sub_id in self.device.get(id, {}).get(DEVICE_STATE,
                                                          {}).keys():
                    self.device[device_id][DEVICE_STATE][
                        sub_id] = cvalue == BOOL_ON
                return id, status
            else:
                return id, {str(sub_id): cvalue == BOOL_ON}

        def parse_switch():
            """ Parse switch """
            id = f"{device}_{room}"
            power_id = f"{WPD_POWER}_{room}"
            if sub_id == 0:
                state = [
                    pvalue[i:i + 18][2:4] == BOOL_ON  #2:4 = bool  4:8 = energy
                    for i in range(0, len(pvalue), 18)
                ]
                power_state = [
                    int(pvalue[i:i + 18][4:8], 16)
                    for i in range(0, len(pvalue), 18)
                ]
                power_status = {}
                for i, v in enumerate(power_state):
                    power_status[str(i + 1)] = v
                self.set_device(power_id, power_status, packet)
                status = {}
                for i, v in enumerate(state):
                    status[str(i + 1)] = v
                return id, status
            else:
                return id, {str(sub_id): pvalue == BOOL_ON}

        def detect_switch():
            """ Detect switch command from wallpad """
            id = f"{device}_{room}"
            # if sub_id == 0:
            #     status = {}
            #     for sub_id in self.device.get(id, {}).get(DEVICE_STATE,
            #                                               {}).keys():
            #         self.device[device_id][DEVICE_STATE][
            #             sub_id] = cvalue == BOOL_ON
            #     return id, status
            # else:
            #     return id, {str(sub_id): cvalue == BOOL_ON}

        def parse_thermostat():
            """ Parse thermostat """
            if p[1] != self.thermo_type:
                self.thermo_type = p[1]
                self.hass.config_entries.async_update_entry(
                    entry=self.entry,
                    data={
                        **self.entry.data, "thermo_type": p[1]
                    })
            id = f"{device}_{sub_id}"
            state = [pvalue[i:i + 6] for i in range(0, len(pvalue), 6)]
            status = {}
            if sub_id == 0:
                for i, v in enumerate(state):
                    if v == "000000": break
                    device_value = {
                        DEVICE_STATE: {
                            THERMO_MODE: THERMO_MODE_PACKET[v[:2]],
                            THERMO_TEMP: int(v[2:4], 16),
                            THERMO_TARGET: int(v[4:6], 16)
                        }
                    }
                    status[str(i + 1)] = device_value
            else:
                v = state[0]
                device_value = {
                    DEVICE_STATE: {
                        THERMO_MODE: THERMO_MODE_PACKET[v[:2]],
                        THERMO_TEMP: int(v[2:4], 16),
                        THERMO_TARGET: int(v[4:6], 16)
                    }
                }
                status = device_value
            return id, status

        def parse_fan():
            """ Parse fan """
            id = f"{device}_{room}"
            state = [pvalue[i:i + 2] for i in range(0, len(pvalue), 2)]
            status = {
                FAN_STATE: FAN_ON if state[0] == BOOL_ON else FAN_OFF,
                FAN_SPEED: FAN_PARSE[state[1]]
            }
            return id, {DEVICE_STATE: status}

        def parse_gas():
            """ Parse gas """
            id = f"{device}_{room}"
            state = [pvalue[i:i + 2] for i in range(0, len(pvalue), 2)]
            return id, {DEVICE_STATE: state[0] == GAS_CLOSE}

        def parse_awaymode():
            """ Parse awaymode """
            id = f"{device}_{sub_id}"
            status = {}
            state = [pvalue[i:i + 4] for i in range(0, len(pvalue), 4)]
            for dv in state:
                d, v = dv[:2], dv[2:4]
                d = WPD_DEVICE.get(d, None)
                v = AWAY_VALUE.get(v, None)
                if d is not None and v is not None:
                    status[d] = v
            return id, {DEVICE_STATE: status}

        def parse_ev():
            """ Parse ev """
            id = f"{device}_{sub_id}"
            if pvalue in ["00", "06"]:
                if pvalue == "00" and ("elevator_1" not in self.device
                                       or self.ev_reg == False):
                    self.ev_reg = True
                    return id, {
                        DEVICE_STATE: {
                            device: False,
                            WPD_EVSENSOR: "대기"
                        }
                    }
                if pvalue == "06":
                    return id, {
                        DEVICE_STATE: {
                            device: False,
                            WPD_EVSENSOR: "호출"
                        }
                    }
            elif len(pvalue) > 2:
                state = [pvalue[i:i + 2] for i in range(0, len(pvalue), 2)]
                status = {device: False, WPD_EVSENSOR: "대기"}
                if state[0] == "00":
                    device_state = self.get_state("elevator_1", DEVICE_STATE)
                    if device_state == True and self.ev_call < 10:
                        self.ev_call += 1
                        _LOGGER.debug(f"[{BRAND}] Wallpad ev call!")
                        self.write("f70b013404411000069aee")
                        return id, {DEVICE_STATE: {WPD_EVSENSOR: "호출"}}
                    elif self.ev_call >= 10:
                        return id, {DEVICE_STATE: status}
                    return None, None
                floor = int(state[1]) if state[1].isdigit() else state[1]
                if floor == 0: floor = "대기"
                status[WPD_EVSENSOR] = floor
                return id, {DEVICE_STATE: status}
            else:
                return None, None

        def parse_usage():
            """ Parse usages """
            if cmd_state not in USAGE_DEVICE: return
            id = f"{device}_{USAGE_DEVICE[cmd_state]}"
            return id, {DEVICE_STATE: int(pvalue)}

        try:
            if cmd == CMD_STATUS:
                if device == WPD_SWITCH and cmd_state in ["40"]:
                    device_id, value = parse_switch()
                elif device == WPD_LIGHT and cmd_state in ["40"]:
                    device_id, value = parse_light()
                elif device == WPD_THERMOSTAT and cmd_state in ["45", "46"]:
                    device_id, value = parse_thermostat()
                elif device == WPD_GAS and cmd_state in ["43"]:
                    device_id, value = parse_gas()
                elif device == WPD_FAN and cmd_state in ["40", "41", "42"]:
                    device_id, value = parse_fan()
                elif device == WPD_EV and cmd_state in ["41"]:
                    device_id, value = parse_ev()
                elif device == WPD_AWAYMODE and cmd_state in ["40"]:
                    device_id, value = parse_awaymode()
                elif device == WPD_USAGE:
                    device_id, value = parse_usage()
                elif device != IGNORE:
                    if packet not in self.grab:
                        self.grab.append(packet)
                        _LOGGER.debug(
                            f"[{BRAND}] Wallpad packet discovery {device} -> cmd:{cmd} cmd_state:{cmd_state} sub:{room}{sub_id} value:{pvalue} -> {packet}"
                        )
            elif cmd == CMD_SCAN:
                if device == WPD_EV and cmd_state in ["41"]:
                    device_id, value = parse_ev()
            elif cmd == CMD_CHANGE and device != IGNORE:
                _LOGGER.debug(
                    f"[{BRAND}] Wallpad command -> {device} {cmd} {packet}")
        except:
            if packet not in self.grab:
                self.grab.append(packet)
                _LOGGER.debug(
                    f"[{BRAND}] Wallpad packet error {device} -> cmd:{cmd} cmd_state:{cmd_state} sub:{room}{sub_id} value:{pvalue} -> {packet}"
                )

        if device_id is not None and value is not None:
            self.set_tick(-self.get_option(OPT_SEND_INT, SEND_INTERVAL) / 1000)
            self.set_device(device_id, value, packet)
        elif device == WPD_EV:
            self.set_tick(-self.get_option(OPT_SEND_INT, SEND_INTERVAL) / 1000)
        else:
            self.set_tick()

    def poll(self, p):
        """ Get packet from tcp/ip socket and validate checksum. """
        if p is not None and isinstance(p, str) and p != "":
            if p == PACKET_HEADER:
                self._flag = True
            if self._flag:
                self._packet.append(p)
            if p == PACKET_TAIL:
                if self.checksum(self._packet):
                    self.parse(self._packet)
                self._packet.clear()
                self._flag = False
