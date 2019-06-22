import sys
from time import time
import mido
import json
from bells import BellsController


# LOAD CONFIG
config = json.load(open('config.json', 'r'))

# Spin up main objects
bells = BellsController(config["Bells"])

if len(sys.argv) > 1:
    portname = sys.argv[1]
else:
    portname = None  # Use default port


cur_note = 0
cur_min = 0
cur_max = 0
prev_value = 0
last_ring = time()

try:
    with mido.open_input(portname) as port:
        print('Using {}\n'.format(port))
        for msg in port:

            # print(vars(msg))

            if msg.type == 'note_on':
                if msg.note == cur_note:
                    # test ring note
                    bells.ring(cur_note, msg.velocity)
                else:
                    # select new note to config
                    cur_note = msg.note
                    cur_min = 0
                    cur_max = 0
                last_ring = time()

            elif msg.type == 'control_change' and cur_note:
                # limit frequency of test rings
                if time() - last_ring > 0.2 and prev_value != msg.value:
                    last_ring = time()
                    prev_value = msg.value
                    if msg.control == 1:
                        bells.config(cur_note, msg.control, msg.value)
                        # set clapper min power
                        bells.ring(cur_note, 0)
                        cur_min = msg.value
                    elif msg.control == 2:
                        bells.config(cur_note, msg.control, msg.value)
                        # set clapper max power
                        bells.ring(cur_note, 127)
                        cur_max = msg.value
                    elif msg.control == 24 and msg.value > 0:
                        bells.config(cur_note, 0xFF, 0)
                        sys.stdout.write(" -- PROGRAMMING EEPROM --            \r")
                        sys.stdout.flush()
                        continue

            sys.stdout.write("Note: {:3} |  min:{:3}  max:{:3}  \r".format(cur_note, cur_min, cur_max))
            sys.stdout.flush()


except KeyboardInterrupt:
    pass

bells.close()
