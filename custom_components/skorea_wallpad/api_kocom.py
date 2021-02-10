import logging
import re
import time
import threading

from homeassistant.components.fan import SPEED_HIGH, SPEED_LOW, SPEED_MEDIUM, SPEED_OFF
from homeassistant.core import callback
from .const import (
    PLATFORMS, WPD_MAIN, WPD_DOORLOCK, WPD_EV, WPD_FAN, WPD_GAS, WPD_LIGHT,
    WPD_MOTION, WPD_SWITCH, WPD_THERMOSTAT, WPD_LIGHTBREAK, WPD_MAIN_LIST,
    FAN_STATE, FAN_OFF, FAN_ON, FAN_SPEED, THERMO_AWAY, THERMO_HEAT,
    THERMO_MODE, THERMO_OFF, THERMO_TARGET, THERMO_TEMP, SIGNAL, SEND_INTERVAL,
    SCAN_INTERVAL, SCAN_LIST, TICK, DEVICE_STATE, DEVICE_INFO, DEVICE_UNIQUE,
    DEVICE_ROOM, DEVICE_GET, DEVICE_SET, DEVICE_REG, DEVICE_UNREG,
    DEVICE_UPDATE, DEVICE_TRY, ENTITY_MAP, DEVICE_ID, DEVICE_NAME, DEVICE_TYPE,
    DEVICE_SUB, CMD_SCAN, CMD_STATUS, CMD_ON, CMD_OFF, CMD_DETECT,
    CLIMATE_DOMAIN, BINARY_SENSOR_DOMAIN, SENSOR_DOMAIN, FAN_DOMAIN,
    SWITCH_DOMAIN, LIGHT_DOMAIN)
_LOGGER = logging.getLogger(__name__)

KOCOM_PTR = re.compile(
    "......(.)(.)..(..)(..)(..)(..)(..)(................)(..)....")
SWITCH_PTR = re.compile("(..)(..)(..)(..)(..)(..)(..)(..)")
THERMO_PTR = re.compile("(.)..(.)(..)..(..)......")
FAN_PTR = re.compile("(..)..(.)...........")

BRAND = "KOCOM"
VERSION = "1.5"
SCAN_LIST = [WPD_LIGHT, WPD_SWITCH, WPD_THERMOSTAT, WPD_GAS, WPD_FAN]

WPD_DEVICE = {
    "00": WPD_MAIN,
    "01": WPD_MAIN,
    "0e": WPD_LIGHT,
    "36": WPD_THERMOSTAT,
    "3b": WPD_SWITCH,
    "2c": WPD_GAS,
    "44": WPD_EV,
    "48": WPD_FAN,
    "60": WPD_MOTION,
    "33": WPD_DOORLOCK
}

CMD = {
    "3a": CMD_SCAN,
    "00": CMD_STATUS,
    "01": CMD_ON,
    "02": CMD_OFF,
    "04": CMD_DETECT
}

FAN = {
    FAN_ON: "1101",
    FAN_OFF: "0001",
    SPEED_LOW: 1,
    SPEED_MEDIUM: 2,
    SPEED_HIGH: 3
}
FAN_SPEED_LIST = [SPEED_OFF, SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH]
THERMO = {THERMO_HEAT: "1100", THERMO_AWAY: "1101", THERMO_OFF: "0100"}

PACKET_HEADER = "aa"
PACKET_LEN = 21
VALUE_TRUE = "ff"
VALUE_FALSE = "00"
DEFAULT_TARGET = 22


def device_to_packet(device):
    for p, d in WPD_DEVICE.items():
        if d == device:
            return p


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
        self.scan_list = SCAN_LIST
        self.tick = time.time()
        self.packet_que = []
        self.device = {}
        self.unique = {}
        self.fail = {}
        self._que = threading.Thread(target=self.loop)
        self._que.daemon = True
        self._que.start()

        self.last_target = {}
        self.thermo_mode = THERMO
        for mode, packet in THERMO.items():
            if self.entry.data.get(mode):
                self.thermo_mode[mode] = packet
        self._packet = []
        self._flag = False

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
        if int(device_room) > 10: return
        if device_id not in self.device:
            self.device[device_id] = {
                TICK: 0 if isInit else time.time() + 5,
                DEVICE_INFO: {},
                DEVICE_STATE: {},
            }
        if sub_id is None: return self.device[device_id]
        if device_type in WPD_MAIN_LIST:
            device_name = f"{self.brand}_{device_type}"
        elif device_type in [WPD_THERMOSTAT]:
            device_name = f"{self.brand}_{device_id}"
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
        self.tick = time.time()
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
            DEVICE_TRY: 0,
            DEVICE_ID: device_id,
            DEVICE_SUB: sub_id,
            DEVICE_STATE: value
        }
        if device_id in self.fail and self.fail[device_id] > 3: return
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
                try:
                    que = self.packet_que[0]
                except:
                    pass
                if (que and now - self.tick > SEND_INTERVAL / 1000
                        and now - que[TICK] > SEND_INTERVAL / 1000):
                    count = que[DEVICE_TRY]
                    device_id = que[DEVICE_ID]
                    sub_id = que[DEVICE_SUB]
                    value = que[DEVICE_STATE]
                    packet = self.make_packet(device_id, sub_id, value)
                    if packet is False: count = 6
                    _LOGGER.debug(
                        f'[{BRAND}] Wallpad packet {"send" if count <= 5 else "failed"}{count if count <= 5 else ""} => {device_id} > {sub_id} > {value} > {packet}'
                    )
                    if count > 5:
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
                    if (now - device[TICK] > SCAN_INTERVAL
                            and device_type in self.scan_list):
                        self.device[device_id][TICK] = now
                        self.queue(device_id, None, CMD_SCAN)

    def set_device(self, device_id, state):
        """
        Set device state from wallpad.\n
        device_id = device+room / state = list|dict
        """
        device_type = device_id.split("_")[0]
        wpd_to_entity = ENTITY_MAP[device_type]
        add_device = SIGNAL[wpd_to_entity]
        if device_id in self.fail: self.fail[device_id] = 0

        def add(did, sid, value):
            """ Add device to entities """
            if did is None: return
            device_info = self.init_device(did, sid, False)
            if value == True or sid.isalpha():
                self.async_add_device(add_device, device_info)

        def update(did, sid, old, new):
            """ Update device state to entities """
            if did is None: return
            unique_id = f"{did}_{sid}"
            if (self.unique.get(unique_id) and old.get(sid) != new):
                update = self.unique[unique_id][DEVICE_UPDATE]
                if update is not None: update()

        if len(self.packet_que) > 0:
            que = self.packet_que[0]
            if ((que[DEVICE_ID] == device_id and que[DEVICE_STATE] == CMD_SCAN)
                    or
                (que[DEVICE_SUB] in state and que[DEVICE_ID] == device_id and
                 (que[DEVICE_STATE] == state[que[DEVICE_SUB]] or
                  (device_type in [WPD_THERMOSTAT] and que[DEVICE_STATE]
                   [THERMO_MODE] == state[que[DEVICE_SUB]][THERMO_MODE]
                   and que[DEVICE_STATE][THERMO_TARGET]
                   == state[que[DEVICE_SUB]][THERMO_TARGET])))):
                self.deque()
        if wpd_to_entity in PLATFORMS:
            for sub_id, value in state.items():
                add(device_id, sub_id, value)
        else:
            _LOGGER.info(
                f"[{BRAND}] Wallpad unknown device {device_id} => {state}")

        if device_id not in self.device: return
        self.device[device_id][TICK] = time.time()
        old_state = self.device[device_id][DEVICE_STATE]
        if old_state != state:
            _LOGGER.debug(f"[{BRAND}] Wallpad {device_id} => {state}")
            if wpd_to_entity in PLATFORMS:
                self.device[device_id][DEVICE_STATE] = state
                for sub_id, value in state.items():
                    update(device_id, sub_id, old_state, value)

    def checksum(self, packet):
        """ Validate checksum > (sum+1)%256 """
        if len(packet) < 18:
            return False
        p_sum = 0
        for i in range(0, 18):
            p_sum += int(packet[i], 16)
        c_sum = '{0:02x}'.format((p_sum + 1) % 256)
        return packet[18] == c_sum

    def makesum(self, packet):
        """ Make checksum > (sum+1)%256 """
        if len(packet) < 18:
            return False
        p_sum = 0
        for i in range(0, 18):
            p_sum += int(packet[i], 16)
        c_sum = '{0:02x}'.format((p_sum + 1) % 256)
        return c_sum

    def make_packet(self, device_id, sub_id, value):
        """ Make packet from device_id, sub_id, value """
        splt = device_id.split("_")
        device = splt[0]
        room = splt[1]
        dev = f"{device_to_packet(device)}{room}"
        wpd = "0100"
        p_value, dst, src, cmd = None, None, None, None

        def make_switch():
            """ Make value packet of light, switch """
            rv = ""
            for i in range(1, 9):
                drs = f"{device}_{room}_{i}"
                dr = f"{device}_{room}"
                if sub_id == "0":
                    if drs in self.unique:
                        pv = VALUE_TRUE if value else VALUE_FALSE
                    else:
                        pv = VALUE_FALSE
                else:
                    if sub_id == str(i):
                        pv = VALUE_TRUE if value else VALUE_FALSE
                    else:
                        pv = VALUE_TRUE if (
                            dr in self.device
                            and str(i) in self.device[dr][DEVICE_STATE]
                            and self.device[dr][DEVICE_STATE][str(i)]
                        ) else VALUE_FALSE
                rv += pv
            return rv

        def make_thermostat():
            """ Make value packet of thermostat """
            # print(device_id, sub_id, value)
            # thermostat_00 state {'mode': 'heat', 'target': 21.0}
            rv = ""
            rv += self.thermo_mode[value[THERMO_MODE]]
            rv += "{0:02x}".format(int(float(value[THERMO_TARGET])))
            rv += "0000000000"
            return rv

        def make_fan():
            """ Make value packet of fan """
            rv = ""
            rv += FAN[value[DEVICE_STATE]]
            rv += "{0:x}".format(int(FAN[value[FAN_SPEED]]) * 4)
            rv += "00000000000"
            return rv

        send_type = "b"
        if value == CMD_SCAN:
            p_value, dst, src, cmd = "0000000000000000", dev, wpd, "3a"
        elif device == WPD_LIGHT and room == "ff":
            send_type = "9"
            if value.get(DEVICE_STATE):
                p_value, dst, src, cmd = "0000000000000000", dev, wpd, "65"
            else:
                p_value, dst, src, cmd = "ffffffffffffffff", dev, wpd, "66"
        elif device in [WPD_LIGHT, WPD_SWITCH]:
            p_value, dst, src, cmd = make_switch(), dev, wpd, "00"
        elif device in [WPD_THERMOSTAT]:
            p_value, dst, src, cmd = make_thermostat(), dev, wpd, "00"
        elif device in [WPD_FAN]:
            p_value, dst, src, cmd = make_fan(), dev, wpd, "00"
        elif device == WPD_GAS:
            p_value, dst, src, cmd = "0000000000000000", dev, wpd, "02"
        elif device == WPD_EV:
            p_value, dst, src, cmd = "0000000000000000", wpd, dev, "01"

        if p_value is None: return False
        packet_str = f"aa5530{send_type}c00{dst}{src}{cmd}{p_value}"
        packet = [packet_str[i:i + 2] for i in range(0, len(packet_str), 2)]
        chksum = self.makesum(packet)
        packet.append(chksum)
        packet.append("0d")
        packet.append("0d")
        if not self.checksum(packet): return False
        return "".join(packet)

    def parse(self, packet):
        """ Parse packet """
        def parse_switch(packet_value):
            """ Parse switch/light """
            state = {}
            pmatch = SWITCH_PTR.match(packet_value)
            all = False
            for i in range(1, 9):
                value = pmatch.group(i) == VALUE_TRUE
                state[str(i)] = value
                all = value if value else all
            state[str(0)] = all
            return state

        def parse_thermostat(device_id, packet_value):
            """ Parse thermostat """
            pmatch = THERMO_PTR.match(packet_value)
            mode_packet = packet_value[:4]
            isOn = pmatch.group(1) == "1"
            isAway = pmatch.group(2) == "1"
            target = int(pmatch.group(3), 16)
            temperature = int(pmatch.group(4), 16)
            mode = ""
            if (isOn and isAway):
                mode = THERMO_AWAY
            elif isOn:
                mode = THERMO_HEAT
            else:
                mode = THERMO_OFF
            if self.thermo_mode[mode] != mode_packet:
                self.thermo_mode[mode] = mode_packet
                self.hass.config_entries.async_update_entry(
                    entry=self.entry,
                    data={
                        **self.entry.data, mode: mode_packet
                    })
            if mode != THERMO_HEAT:
                last = self.entry.data.get(device_id)
                target = last if last else DEFAULT_TARGET
                self.last_target[device_id] = target
            state = {
                THERMO_MODE: mode,
                THERMO_TARGET: target,
                THERMO_TEMP: temperature
            }
            if (device_id in self.last_target
                    and self.last_target[device_id] != target):
                self.last_target[device_id] = target
                self.hass.config_entries.async_update_entry(
                    entry=self.entry,
                    data={
                        **self.entry.data, device_id: target
                    })
            return {DEVICE_STATE: state}

        def parse_fan(packet_value):
            """ Parse fan """
            pmatch = FAN_PTR.match(packet_value)
            isOn = pmatch.group(1) == "11"
            speed = FAN_SPEED_LIST[int((int(pmatch.group(2), 16) / 4))]
            state = {FAN_STATE: isOn, FAN_SPEED: speed}
            return {DEVICE_STATE: state}

        packet = "".join(packet)
        pmatch = KOCOM_PTR.match(packet)
        # KOCOM_PTR = re.compile("......(.)(.)..(..)(..)(..)(..)(..)(................)(..)....")
        p = {
            "pt": pmatch.group(1),
            "count": pmatch.group(2),
            "dd": pmatch.group(3),
            "dr": pmatch.group(4),
            "sd": pmatch.group(5),
            "sr": pmatch.group(6),
            "cmd": pmatch.group(7),
            "value": pmatch.group(8),
            "sum": pmatch.group(9)
        }
        wpd, dst, src = ["0000", "0100"], p["dd"] + p["dr"], p["sd"] + p["sr"]
        cmd = CMD[p["cmd"]] if p["cmd"] in CMD else False
        if p["pt"] == "d" and src in wpd:
            _LOGGER.debug(
                f'[{BRAND}] Wallpad packet income [{src} -> {dst}] [{cmd}] [{p["value"]}] => {packet}'
            )
            device = WPD_DEVICE[p["dd"]] if p["dd"] in WPD_DEVICE else False
            room = p["dr"]
            value = None
            device_id = f'{device}_{room}'
            if device and cmd == CMD_STATUS:
                if device in [WPD_LIGHT, WPD_SWITCH]:
                    value = parse_switch(p["value"])
                elif device == WPD_THERMOSTAT:
                    value = parse_thermostat(device_id, p["value"])
                elif device == WPD_FAN:
                    value = parse_fan(p["value"])
            elif device == WPD_GAS and (cmd in [CMD_ON, CMD_OFF]):
                value = {DEVICE_STATE: cmd != CMD_ON}
            elif device == WPD_MOTION and cmd == CMD_DETECT:
                value = {DEVICE_STATE: p["value"] != "0100000000000000"}
            if value is not None:
                self.set_device(device_id, value)
        elif p["pt"] == "b" and dst in wpd:
            _LOGGER.debug(
                f'[{BRAND}] Wallpad packet income [{src} -> {dst}] [{cmd}] [{p["value"]}] => {packet}'
            )
            device = WPD_DEVICE[p["sd"]] if p["sd"] in WPD_DEVICE else False
            room = p["sr"]
            value = None
            device_id = f'{device}_{room}'
            if device == WPD_EV and cmd == CMD_ON:
                value = {DEVICE_STATE: True}
            if value is not None:
                self.set_device(device_id, value)
        elif p["pt"] == "b" and src in wpd:
            _LOGGER.debug(
                f'[{BRAND}] Wallpad packet income [{src} -> {dst}] [{cmd}] [{p["value"]}] => {packet}'
            )
            device = WPD_DEVICE[p["dd"]] if p["dd"] in WPD_DEVICE else False
            room = p["dr"]
            value = None
            device_id = f'{device}_{room}'
            if device and cmd == CMD_SCAN:
                _LOGGER.debug(f"[{BRAND}] Wallpad device scan => {device_id}")
            elif device == WPD_EV and cmd == CMD_ON:
                value = {DEVICE_STATE: False}
            if value is not None:
                self.set_device(device_id, value)
        elif p["pt"] == "9" and src in wpd:
            _LOGGER.debug(
                f'[{BRAND}] Wallpad packet income [{src} -> {dst}] [{cmd}] [{p["value"]}] => {packet}'
            )
            device = WPD_DEVICE[p["dd"]] if p["dd"] in WPD_DEVICE else False
            room = p["dr"]
            value = {DEVICE_STATE: cmd == "65"}
            device_id = f'{device}_{room}'
            self.set_device(device_id, value)
        elif (not WPD_DEVICE.get(p["dd"]) or not WPD_DEVICE.get(p["sd"])
              or not CMD.get(p["cmd"])):
            _LOGGER.info(
                f'[{BRAND}] Wallpad packet discovery [{src} -> {dst}] [{cmd}] [{p["value"]}] => {packet}'
            )

    def poll(self, p):
        """ Get packet from tcp/ip socket and validate checksum. """
        if p is not None and isinstance(p, str) and p != "":
            if p == PACKET_HEADER:
                self._flag = True
            if self._flag:
                self._packet.append(p)
            if len(self._packet) >= PACKET_LEN:
                if self.checksum(self._packet):
                    self.parse(self._packet)
                self._packet.clear()
                self._flag = False
