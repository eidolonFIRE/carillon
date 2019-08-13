from bells import BellsController
from leds import LightController
from config import Config
import sys
import os
import mido
from mido.sockets import PortServer
import threading
import signal
from time import sleep


# Spin up main objects
config = Config("config.json")
bells = BellsController(config)
leds = LightController(config)

leds.text_cmd("start: fade_to_color")
leds.text_cmd("start: note_pulse_gradient hold=true")

config.transpose = 0
config.playback_speed = 1.0
config.playback_volume = 1.0

ALIVE = True


def sigint_handler(signal, frame):
    global ALIVE
    ALIVE = False
    print("Keyboard Interrupt")


def handle_midi_event(msg):
    # print(msg)
    if hasattr(msg, "text"):
        leds.text_cmd(msg.text)

    if hasattr(msg, "note"):
        msg.note += config.transpose

    if msg.type == 'note_on' and msg.velocity > 0:
        bells.ring(msg.note, max(1, int(msg.velocity * config.playback_volume)))
    elif msg.type == 'note_off' or (hasattr(msg, "velocity") and msg.velocity == 0):
        bells.damp(msg.note)

    if msg.type == 'control_change':
        if msg.control == 64:
            bells.sustain = msg.value >= 64
        elif msg.control == 5:
            config.playback_volume = min(1.0, msg.value / 127.0)
            print("Volume: {:.2}x".format(config.playback_volume))

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


def thread_device_input(port):
    global ALIVE
    for msg in port:
        handle_midi_event(msg)
        if not ALIVE or port.closed:
            return


def thread_device_monitor():
    global ALIVE
    while ALIVE:
        # scan list
        port_options = list(filter(lambda x: "Through" not in x, mido.get_input_names()))
        portname = port_options[0] if len(port_options) else None

        if portname:
            with mido.open_input(portname) as port:
                print("Device connected: {}".format(portname))
                thread_device = threading.Thread(target=thread_device_input, daemon=True, args=(port,))
                thread_device.start()
                while ALIVE and portname in mido.get_input_names():
                    sleep(5)
                port.close()
                thread_device.join(1)
                print("Device disconnected: {}".format(portname))
        sleep(5)


def thread_play_file(filename):
    global ALIVE
    midifile = mido.MidiFile(filename)
    midifile.ticks_per_beat *= config.playback_speed

    print("Midi file type: {}".format(midifile.type))
    print("Expected play time: {:.2f}".format(midifile.length * config.playback_speed))
    for i, track in enumerate(midifile.tracks):
        print('Track {}: {}'.format(i, track.name))

    for msg in midifile.play(meta_messages=True):
        handle_midi_event(msg)
        if not ALIVE:
            print("Thread: closing play_file")
            return

    ALIVE = False


def thread_midi_server(port):
    global ALIVE
    print("Thread: starting midi_server (localhost:{})".format(port))
    with PortServer('localhost', port) as server:
        while True:
            client = server.accept()
            try:
                for message in client:
                    # print(message)
                    handle_midi_event(message)
                    if not ALIVE:
                        print("Thread: closing midi_server")
                        return
            except:
                print("midi client disconnected")


# /////////////////////////// MAIN ///////////////////////////
def main():
    thread_leds = threading.Thread(target=thread_update_leds)
    thread_leds.start()
    thread_device = threading.Thread(target=thread_device_monitor, daemon=True)
    thread_device.start()
    thread_server = threading.Thread(target=thread_midi_server, daemon=True, args=(9080,))
    thread_server.start()

    # detect OS and load gpio pedals if on raspberry pi
    os_type = " ".join(os.uname())
    if "raspberrypi" in os_type or "arm" in os_type:
        from gpiozero import Button
        damp_pedal = Button("GPIO17")
        mort_pedal = Button("GPIO27")
        damp_pedal.when_pressed = bells.pedal_sustain_on
        damp_pedal.when_released = bells.pedal_sustain_off
        mort_pedal.when_pressed = bells.pedal_mortello_on
        mort_pedal.when_released = bells.pedal_mortello_off

    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        # PLAY A MIDI FILE
        thread_file = threading.Thread(target=thread_play_file, daemon=True, args=(sys.argv[1],))
        thread_file.start()
        thread_file.join()

    thread_leds.join()
    bells.close()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigint_handler)
    main()
