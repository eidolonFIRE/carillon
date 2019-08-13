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
        self.num_bells = config["Bells"]["num_bells"]
        self.midi_offset = config["Bells"]["midi_offset"]
        self._sustain = False
        self._sustain_notes = set()
        self.mortello = False

        # open serial ouput
        self.tty = serial.Serial(config["Bells"]["control_tty"], int(config["Bells"]["control_baud"]), bytesize=8, parity='N', stopbits=1)

        # push calibration to bells
        for idx, each in enumerate(config._config_file["Bells"]["calibration"]):
            self.set_clapper_min(idx + self.midi_offset, each[0])
            self.set_clapper_max(idx + self.midi_offset, each[1])

    def _tx(self, address, cmd, value):
        assert cmd.value is not 0x0, "Command value 0x0 is reserved!"
        self.tty.write(bytes([0xC0 | (address & 0x3F), cmd.value & 0x7F, value & 0x7F]))

    """ -------------------------- PUBLIC API -------------------------- """

    def pedal_sustain_on(self):
        self._sustain = True

    def pedal_sustain_off(self):
        self._sustain = False
        for each in self._sustain_notes:
            self.damp(each)
        self._sustain_notes = set()

    @property
    def sustain(self):
        return self._sustain

    @sustain.setter
    def sustain(self, value):
        if value:
            self.pedal_sustain_on()
        else:
            self.pedal_sustain_off()

    def pedal_mortello_on(self):
        self.mortello = True

    def pedal_mortello_off(self):
        self.mortello = False

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
        if self.mortello:
            self.damp(note, duration=0xF)
            self._tx(self.map_note(note), BellCommand.RING_M, velocity)
        else:
            self._tx(self.map_note(note), BellCommand.RING, velocity)
        self.last_rung[note] = time()

    def damp(self, note, duration=None):
        if self.sustain:
            self._sustain_notes.add(note)
        else:
            if duration is None:
                if note in self.last_rung.keys():
                    duration = min(0x1F, max(0xC, int(0x1F - 8 * (time() - self.last_rung[note]))))
                else:
                    duration = 0
            self._tx(self.map_note(note), BellCommand.DAMP, duration)

    def set_clapper_min(self, note, value):
        self._tx(self.map_note(note), BellCommand.SET_CLAPPER_MIN, value)

    def set_clapper_max(self, note, value):
        self._tx(self.map_note(note), BellCommand.SET_CLAPPER_MAX, value)

    def commit_eeprom(self, note):
        self._tx(self.map_note(note), BellCommand.COMMIT_E2, 0x1D)

    def close(self):
        self.tty.close()
