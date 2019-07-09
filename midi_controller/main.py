from bells import BellsController
from leds import LightController
from config import Config
import sys
import os
import mido
import threading
import signal
from time import sleep


# Spin up main objects
config = Config("config.json")
bells = BellsController(config)
leds = LightController(config)

config.transpose = 0
config.playback_speed = 1.0
config.playback_volume = 0.3

ALIVE = True


def sigint_handler(signal, frame):
    global ALIVE
    ALIVE = False
    print("Keyboard Interrupt")


def handle_midi_event(msg):
    if hasattr(msg, "text"):
        leds.text_cmd(msg.text)

    if hasattr(msg, "note"):
        msg.note += config.transpose

    if msg.type == 'note_on' and msg.velocity > 0:
        bells.ring(msg.note, max(1, int(msg.velocity * config.playback_volume)))
    elif msg.type == 'note_off' or (hasattr(msg, "velocity") and msg.velocity == 0):
        if not bells.sustain:
            bells.damp(msg.note)

    if msg.type == 'control_change':
        if msg.control == 64:
            bells.sustain = msg.value >= 64

    if hasattr(msg, "note"):
        msg.note = bells.map_note(msg.note)
        leds.event(msg)


def thread_update_leds():
    global ALIVE
    # global leds
    print("Starting led_update_loop")
    while ALIVE:
        leds.step()
        sleep(1.0 / 100)
    print("Thread: closing update_leds")
    leds.close()


def thread_device_input():
    global ALIVE
    port_options = list(filter(lambda x: "Through" not in x, mido.get_input_names()))
    portname = port_options[0] if len(port_options) else None
    with mido.open_input(portname) as port:
        print('Using {}'.format(port))
        print('Waiting for messages...')
        for msg in port:
            print(msg)
            handle_midi_event(msg)
            if not ALIVE:
                print("Thread: closing device_input")
                return


def thread_play_file(filename):
    global ALIVE
    midifile = mido.MidiFile(filename)
    midifile.ticks_per_beat *= config.playback_speed

    print("Midi file type: {}".format(midifile.type))
    print("Expected play time: {:.2f}".format(midifile.length * config.playback_speed))
    for i, track in enumerate(midifile.tracks):
        print('Track {}: {}'.format(i, track.name))

    for msg in midifile.play(meta_messages=True):
        # print(msg)
        handle_midi_event(msg)
        if not ALIVE:
            print("Thread: closing play_file")
            return

    ALIVE = False


# /////////////////////////// MAIN ///////////////////////////
def main():
    thread_leds = threading.Thread(target=thread_update_leds)
    thread_leds.start()
    thread_device = threading.Thread(target=thread_device_input, daemon=True)
    thread_device.start()

    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        # PLAY A MIDI FILE
        thread_file = threading.Thread(target=thread_play_file, daemon=True, args=(sys.argv[1],))
        thread_file.start()
        thread_file.join()

    thread_leds.join()
    # thread_device.join()
    bells.close()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigint_handler)
    main()
