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
    def __init__(self, config, is_raspberry=True):
        super(BellsController, self).__init__()

        self.config = config

        # initial states
        self.last_rung = {}
        self._sustain = False
        self._sustain_notes = set()
        self.mortello = False

        # open serial ouput
        if is_raspberry:
            self.tty = serial.Serial(config["Bells"]["control_tty"], int(config["Bells"]["control_baud"]), bytesize=8, parity='N', stopbits=1)
        else:
            # stub out serial api
            self.tty = None
            self._tx = self._tx_stub

        # push calibration to bells
        for idx, each in enumerate(config["Bells"]["calibration"]):
            self.set_clapper_min(idx + self.config.midi_offset, each[0])
            self.set_clapper_max(idx + self.config.midi_offset, each[1])

    def _tx_stub(self, address, cmd, value):
        pass

    def _tx(self, address, cmd, value):
        assert cmd.value is not 0x0, "Command value 0x0 is reserved!"
        self.tty.write(bytes([0xC0 | (self.config.map_note(address) & 0x3F), cmd.value & 0x7F, value & 0x7F]))

    """ -------------------------- PUBLIC API -------------------------- """

    def handle_midi_event(self, msg):
        # print(msg)
        if hasattr(msg, "note"):
            msg.note += self.config.transpose

        if msg.type == 'note_on' and msg.velocity > 0:
            self.ring(msg.note, msg.velocity)
        elif msg.type == 'note_off' or (hasattr(msg, "velocity") and msg.velocity == 0):
            self.damp(msg.note)

        if msg.type == 'control_change':
            if msg.control == 64:
                self.sustain = msg.value >= 64
            elif msg.control == 5:
                self.config.volume = min(1.0, msg.value / 127.0)
                print("Volume: {:.2}x".format(self.config.volume))

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

    def ring(self, note, velocity):
        velocity = self.config.map_velocity(velocity)
        if self.mortello:
            self.damp(note, duration=0xF)
            self._tx(note, BellCommand.RING_M, velocity)
        else:
            self._tx(note, BellCommand.RING, velocity)
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
            self._tx(note, BellCommand.DAMP, duration)

    def set_clapper_min(self, note, value):
        self._tx(note, BellCommand.SET_CLAPPER_MIN, value)

    def set_clapper_max(self, note, value):
        self._tx(note, BellCommand.SET_CLAPPER_MAX, value)

    def commit_eeprom(self, note):
        self._tx(note, BellCommand.COMMIT_E2, 0x1D)

    def close(self):
        if self.tty:
            self.tty.close()
