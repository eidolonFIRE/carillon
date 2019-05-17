import sys
import mido
from bells import BellsController

bells = BellsController()

if len(sys.argv) > 1:
    portname = sys.argv[1]
else:
    portname = "MPKmini2:MPKmini2 MIDI 1 24:0"


try:
    with mido.open_input(portname) as port:
        print('Using {}\n'.format(port))
        for msg in port:

            # print(vars(msg))
            if msg.type == 'note_on':
                bells.set_address(msg.note)
                print("Set bell address to: %d" % msg.note)

except KeyboardInterrupt:
    pass

bells.close()
