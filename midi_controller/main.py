from bells import BellsController
from leds import LightController
import sys
import mido
import threading
import json
from time import sleep


# LOAD CONFIG
config = json.load(open('config.json', 'r'))

# Spin up main objects
bells = BellsController(config["Bells"])
leds = LightController(config["Leds"])




ALIVE = True


def led_update_loop():
    global ALIVE
    global leds
    print("Starting led_update_loop")
    while ALIVE:
        leds.step()
        sleep(1.0 / 60)


led_thread = threading.Thread(target=led_update_loop)
led_thread.start()

leds.start_patch("note_pulse")

if len(sys.argv) > 1:
    portname = sys.argv[1]
else:
    portname = "MPKmini2:MPKmini2 MIDI 1 24:0"  # Use default port

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

            msg.note -= int(config["Bells"]["midi_offset"])
            leds.event(msg)


except KeyboardInterrupt:
    pass

ALIVE = False

bells.close()
led_thread.join()
