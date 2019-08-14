from time import time
import mido
from bells import BellsController
from config import Config
import json


# LOAD CONFIG
config = Config("config.json")

# Spin up main objects
bells = BellsController(config)

port_options = list(filter(lambda x: "Through" not in x, mido.get_input_names()))
portname = port_options[0] if len(port_options) else None


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

saved = set()
note_min = {}
note_max = {}
note_min_original = {}
note_max_original = {}

# load from file
midi_offset = int(config["Bells"]["midi_offset"])
for idx, each in enumerate(config["Bells"]["calibration"]):
    note_min[idx + midi_offset] = each[0]
    note_max[idx + midi_offset] = each[1]
    note_min_original[idx + midi_offset] = each[0]
    note_max_original[idx + midi_offset] = each[1]

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
            elif msg.type == 'note_off' or (hasattr(msg, "velocity") and msg.velocity == 0):
                bells.damp(msg.note)

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

            print(cl.bold + cl.f.lightgrey + "\nSaved Note)   Min    -  Max   \n" + cl.reset + "-" * 30)
            for note in range(bells.midi_offset, bells.midi_offset + 27):
                min_dif = note_min.get(note, 0) - note_min_original.get(note, 0)
                max_dif = note_max.get(note, 0) - note_max_original.get(note, 0)

                print("{}{}{:^6}{:3})  {}{:3} {}{:3} {}- {:3} {}{:3}".format(
                    cl.bold if note == cur_note else cl.reset,
                    cl.f.lightgreen if note in saved else cl.f.lightgrey,
                    "[X]" if note in saved else "[ ]",
                    ("> " if note == cur_note else "  ") + str(note),
                    cl.reset,
                    note_min.get(note, ""),
                    cl.f.lightred if min_dif < 0 else cl.f.lightgreen,
                    "{:+2}".format(min_dif) if min_dif != 0 else "",
                    cl.reset,
                    note_max.get(note, ""),
                    cl.f.lightred if max_dif < 0 else cl.f.lightgreen,
                    "{:+2}".format(max_dif) if max_dif != 0 else "",
                ))
            print(cl.reset)

except KeyboardInterrupt:
    # save config to file
    config["Bells"]["calibration"] = [
        ([note_min.get(x, 0), note_max.get(x, 0)] if x in saved else [note_min_original.get(x, 0), note_max_original.get(x, 0)])
        for x in range(midi_offset, midi_offset + 27)]
    outFile = open("config.json", "w")
    outFile.write(json.dumps(config._config_file, indent=4))

bells.close()
