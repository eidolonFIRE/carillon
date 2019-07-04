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


class cl:
    reset = '\033[0m'
    bold = '\033[01m'
    disable = '\033[02m'
    underline = '\033[04m'
    reverse = '\033[07m'
    strikethrough = '\033[09m'
    invisible = '\033[08m'

    class f:
        black = '\033[30m'
        red = '\033[31m'
        green = '\033[32m'
        orange = '\033[33m'
        blue = '\033[34m'
        purple = '\033[35m'
        cyan = '\033[36m'
        lightgrey = '\033[37m'
        darkgrey = '\033[90m'
        lightred = '\033[91m'
        lightgreen = '\033[92m'
        yellow = '\033[93m'
        lightblue = '\033[94m'
        pink = '\033[95m'
        lightcyan = '\033[96m'

    class b:
        black = '\033[40m'
        red = '\033[41m'
        green = '\033[42m'
        orange = '\033[43m'
        blue = '\033[44m'
        purple = '\033[45m'
        cyan = '\033[46m'
        lightgrey = '\033[47m'


cur_note = -1
prev_value = 0
last_ring = time()

note_min = {}
note_max = {}

saved = set()

try:
    with mido.open_input(portname) as port:
        print('Using {}\n'.format(port))
        for msg in port:

            # print(vars(msg))

            if msg.type == 'note_on':
                if msg.note != cur_note:
                    # select new note to config
                    cur_note = msg.note

                bells.ring(cur_note, msg.velocity)
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
                        note_min[cur_note] = msg.value
                        if cur_note in saved:
                            saved.remove(cur_note)
                    elif msg.control == 2:
                        # set clapper max power
                        bells.set_clapper_max(cur_note, msg.value)
                        bells.ring(cur_note, 127)
                        note_max[cur_note] = msg.value
                        if cur_note in saved:
                            saved.remove(cur_note)
                    elif msg.control == 24 and msg.value > 0:
                        # SAVE to eeprom
                        bells.commit_eeprom(cur_note)
                        saved.add(cur_note)

            print(cl.bold + cl.f.lightgrey + "\nNote - Min - Max")
            for note in range(bells.midi_offset, bells.midi_offset + 27):
                if note == cur_note:
                    string = cl.bold
                else:
                    string = cl.reset

                if note in saved:
                    string += cl.f.lightgreen
                else:
                    string += cl.f.lightgrey
                string += "{:3}) - {:3} - {:3}".format(note, note_min.get(note, ""), note_max.get(note, ""))
                print(string)


except KeyboardInterrupt:
    pass

bells.close()
