import serial
from time import time


class BellsController(object):
    """Hardware controller for Bells"""
    def __init__(self,
                 tty=None,
                 num_bells=27,
                 midi_offset=48):
        super(BellsController, self).__init__()

        # initial states
        self.last_rung = {}
        self.num_bells = num_bells
        self.midi_offset = midi_offset

        # open serial ouput
        if tty:
            self.tty = serial.Serial(tty, 38400)
        else:
            try:
                self.tty = serial.Serial('/dev/ttyUSB1', 38400)
            except:
                self.tty = serial.Serial('/dev/ttyUSB2', 38400)

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

    ''' PUBLIC API '''

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
