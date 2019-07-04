import serial
from time import time
from enum import Enum


class BellCommand(Enum):
    RESERVED = 0x0
    RING = 0x1
    RING_M = 0x2
    DAMP = 0x3
    SET_CLAPPER_MIN = 0x10
    SET_CLAPPER_MAX = 0x20
    COMMIT_E2 = 0x30


class BellsController(object):
    """Hardware controller for Bells"""
    def __init__(self, config):
        super(BellsController, self).__init__()

        # initial states
        self.last_rung = {}
        self.num_bells = config["num_bells"]
        self.midi_offset = config["midi_offset"]

        # open serial ouput
        self.tty = serial.Serial(config["control_tty"], int(config["control_baud"]), bytesize=8, parity='N', stopbits=1)

    def _tx(self, address, cmd, value):
        assert cmd is not 0x0, "Command value 0x0 is reserved!"
        self.tty.write(bytes([0xC0 | (address & 0x3F), cmd & 0x7F, value & 0x7F]))

    """ -------------------------- PUBLIC API -------------------------- """

    def map_note(self, note):
        # bell index from midi note
        address = note - self.midi_offset
        # wrap note into supported octaves
        while address < 0:
            address += 12
        while address >= self.num_bells:
            address -= 12
        return address

    def ring(self, note, velocity):
        self._tx(self.map_note(note), BellCommand.RING, velocity)
        self.last_rung[note] = time()

    def damp(self, note, duration=None):
        if duration is None:
            if note in self.last_rung.keys():
                duration = min(0x1F, max(0xC, int(0x1F - 8 * (time() - self.last_rung[note]))))
            else:
                duration = 0
        self._tx(self.map_note(note), BellCommand.DAMP, 0x40 + duration)

    def mortello(self, note, velocity):
        self.damp(note, duration=0xF)
        self._tx(self.map_note(note), BellCommand.RING_M, velocity)

    def set_clapper_min(self, note, value):
        self._tx(self.map_note(note), BellCommand.SET_CLAPPER_MIN, value)

    def set_clapper_max(self, note, value):
        self._tx(self.map_note(note), BellCommand.SET_CLAPPER_MAX, value)

    def commit_eeprom(self, note):
        self._tx(self.map_note(note), BellCommand.COMMIT_E2, 0x1D)

    def close(self):
        self.tty.close()
