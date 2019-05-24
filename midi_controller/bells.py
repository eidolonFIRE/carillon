import serial
from time import time
from enum import Enum


class BellParam(Enum):
    MIN_CLAP_VALUE = 0x01
    MAX_CLAP_VALUE = 0x02
    SET_ADDRESS = 0x03
    COMMIT_EEPROM_DATA = 0xFF


class BellsController(object):
    """Hardware controller for Bells"""
    def __init__(self, config):
        super(BellsController, self).__init__()

        # initial states
        self.last_rung = {}
        self.num_bells = config["num_bells"]
        self.midi_offset = config["midi_offset"]

        # open serial ouput
        self.tty = serial.Serial(config["control_tty"], int(config["control_baud"]))

    def _map_note(self, note):
        # bell index from midi note
        address = note - self.midi_offset
        # wrap note into supported octaves
        while address < 0:
            address += 12
        while address > self.num_bells:
            address -= 12
        return address

    def _send_note(self, note, cmd):
        address = self._map_note(note)
        self.tty.write(chr(0x80 | (address & 0x3F)))
        self.tty.write(chr(cmd & 0x7F))

    def _send_config(self, note, param, value):
        address = self._map_note(note)
        assert param > 0, "Param value 0x0 is reserved!"
        self.tty.write(chr(0xC0 | (address & 0x3F)))
        self.tty.write(chr(param & 0x7F))
        self.tty.write(chr(value & 0x7F))

    """ PUBLIC API """

    def set_address(self, new_note):
        self._send_config(0x0, BellParam.SET_ADDRESS.value, new_note - self.midi_offset)

    def ring(self, note, velocity):
        self._send_note(note, (velocity >> 1) & 0x3F)
        self.last_rung[note] = time()

    def damp(self, note, duration=None):
        if duration is None:
            duration = min(0x3F, max(4, int(0x3F - 10 * (time() - self.last_rung[note]))))
        self._send_note(note, 0x40 | (duration & 0x3F))

    def mortello(self, note, velocity):
        self.damp(note, duration=1)
        self.ring(note, velocity)

    def config(self, note, param, value):
        self._send_config(note, param, value)

    def close(self):
        self.tty.close()
