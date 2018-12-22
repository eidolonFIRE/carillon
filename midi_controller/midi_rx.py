import sys
import mido
import os


tty = os.open("/dev/ttyUSB1", os.O_RDWR)

if len(sys.argv) > 1:
    portname = sys.argv[1]
else:
    portname = None  # Use default port


def _send_cmd(address, cmd):
    os.write(tty, chr(0x80 | (address & 0x3F)))
    os.write(tty, chr(cmd & 0x7F))


def ring(note, velocity):
    _send_cmd(note, velocity & 0x1F)


def damp(note, time):
    _send_cmd(note, (1 << 5) | (time & 0x1F))


try:
    with mido.open_input(portname) as port:
        print('Using {}'.format(port))
        print('Waiting for messages...')
        for msg in port:

            print(vars(msg))

            if msg.type == 'note_on':
                ring(msg.note - 48, msg.velocity >> 2)

            elif msg.type == 'note_off':
                damp(msg.note - 48, 8)


except KeyboardInterrupt:
    pass
