import sys
import mido
from bells import BellsController

bells = BellsController()

if len(sys.argv) > 1:
    portname = sys.argv[1]
else:
    portname = None  # Use default port

try:
    with mido.open_input(portname) as port:
        print('Using {}'.format(port))
        print('Waiting for messages...')
        for msg in port:

            print(vars(msg))

            if msg.type == 'note_on':
                bells.ring(msg.note, msg.velocity)

            elif msg.type == 'note_off':
                bells.damp(msg.note)


except KeyboardInterrupt:
    pass

bells.close()
