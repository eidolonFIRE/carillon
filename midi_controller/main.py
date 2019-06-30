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


config["transpose"] = 0
config["playback_speed"] = 1.0
config["playback_volume"] = 0.3


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

leds.start_patch("rainbow")

if len(sys.argv) > 1:
    portname = sys.argv[1]
else:
    portname = "MPKmini2:MPKmini2 MIDI 1 24:0"  # Use default port


if len(sys.argv) > 2 and len(sys.argv[2]):
    # PLAY A MIDI FILE
    try:
        midifile = mido.MidiFile(sys.argv[2])
        midifile.ticks_per_beat *= config["playback_speed"]

        print('expected play time: {:.2f}'.format(midifile.length * config["playback_speed"]))

        for msg in midifile.play():
            # print(vars(msg))

            if hasattr(msg, "note"):
                msg.note += config["transpose"]
                # print(msg.note)

            if msg.type == 'note_on' and msg.velocity > 0:
                bells.ring(msg.note, max(1, int(msg.velocity * config["playback_volume"])))
            elif msg.type == 'note_off' or (hasattr(msg, "velocity") and msg.velocity == 0):
                bells.damp(msg.note)
                pass

            if hasattr(msg, "note"):
                msg.note = bells._map_note(msg.note)
                leds.event(msg)
    except KeyboardInterrupt:
        pass


else:
    # PLAY FROM KEYBOARD
    try:
        with mido.open_input(portname) as port:
            print('Using {}'.format(port))
            print('Waiting for messages...')
            for msg in port:
                print(vars(msg))
                if hasattr(msg, "note"):
                    msg.note += config["transpose"]
                if msg.type == 'note_on':
                    bells.ring(msg.note, msg.velocity)
                    # bells.mortello(msg.note, msg.velocity)
                elif msg.type == 'note_off':
                    bells.damp(msg.note)
                    # pass
                if hasattr(msg, "note"):
                    msg.note = bells._map_note(msg.note)
                    leds.event(msg)
    except KeyboardInterrupt:
        pass


ALIVE = False

bells.close()
# led_thread.join()
