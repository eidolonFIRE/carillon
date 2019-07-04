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

note_min = {}
note_max = {}

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
                if time() - last_ring > 0.3 and prev_value != msg.value:
                    last_ring = time()
                    prev_value = msg.value
                    if msg.control == 1:
                        # set clapper min power
                        bells.set_clapper_min(cur_note, msg.value)
                        bells.ring(cur_note, 0)
                        cur_min = msg.value
                        note_min[cur_note] = msg.value
                    elif msg.control == 2:
                        # set clapper max power
                        bells.set_clapper_max(cur_note, msg.value)
                        bells.ring(cur_note, 127)
                        cur_max = msg.value
                        note_max[cur_note] = msg.value
                    elif msg.control == 24 and msg.value > 0:
                        # SAVE to eeprom
                        bells.commit_eeprom(cur_note)

                print("Note - Min - Max")
                for note in range(27):
                    print("{:3} - {:3} - {:3}".format(cur_note, cur_min, cur_max))


except KeyboardInterrupt:
    pass

bells.close()
