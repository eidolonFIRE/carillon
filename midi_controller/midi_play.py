import sys
import mido
import time
from mido import MidiFile

import serial

try:
    tty = serial.Serial('/dev/ttyUSB1', 9600)
except:
    tty = serial.Serial('/dev/ttyUSB2', 9600)


filename = sys.argv[1]
if len(sys.argv) == 3:
    portname = sys.argv[2]
else:
    portname = None


def _send_cmd(address, cmd):
    tty.write(chr(0x80 | (address & 0x3F)))
    tty.write(chr(cmd & 0x7F))


def ring(note, velocity):
    _send_cmd(note, velocity & 0x1F)


def damp(note, time):
    _send_cmd(note, (1 << 5) | (time & 0x1F))



with mido.open_output(portname) as output:
    try:
        midifile = MidiFile(filename)
        t0 = time.time()
        for msg in midifile.play():
            print(msg)
            # output.send(msg)

            if msg.type == 'note_on':
                ring(msg.note - 48, max(1, (msg.velocity >> 2)))

            elif msg.type == 'note_off':
                damp(msg.note - 48, 8)
        print('play time: {:.2f} s (expected {:.2f})'.format(
                time.time() - t0, midifile.length))

    except KeyboardInterrupt:
        print()
        output.reset()
