from bells import BellsController
from config import Config
from leds import LightController
from mido.sockets import PortServer
from time import sleep
import difflib
import mido
import multiprocessing as mp
import os
import pyudev
import re
import signal
import socket
import socketserver
import threading

# Spin up main objects
config = Config("config.json")
bells = BellsController(config)
leds = LightController(config)
leds.text_cmd("add fade_to_color")
leds.text_cmd("add note_pulse_gradient hold=true")
leds.cmd_queue = mp.Queue()
leds.midi_queue = mp.Queue()

config.transpose = 0
config.playback_speed = 1.0
config.playback_volume = 1.0

ALIVE = True
HALT_PLAYBACK = False

# get my local IP address
_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_s.connect(("8.8.8.8", 80))
MY_IP = _s.getsockname()[0]
_s.close()

_os_type = " ".join(os.uname())
IS_RASPBERRY = "raspberrypi" in _os_type or "arm" in _os_type


def sigint_handler(signal, frame):
    global ALIVE
    ALIVE = False
    print("Keyboard Interrupt")


def handle_midi_event(msg):
    if hasattr(msg, "text"):
        leds.cmd_queue.put(msg.text)
    bells.handle_midi_event(msg)
    if hasattr(msg, "note"):
        msg.note = bells.map_note(msg.note)
        leds.midi_queue.put(msg)


def thread_device_input(midi_port):
    global ALIVE
    for msg in midi_port:
        handle_midi_event(msg)
        if not ALIVE or midi_port.closed:
            return


def wait_for_usb_change():
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem='usb')
    for device in iter(monitor.poll, None):
        # print(device.action, device)
        return


def thread_device_monitor():
    global ALIVE
    while ALIVE:
        # scan list
        port_options = list(filter(lambda x: "Through" not in x, mido.get_input_names()))
        portname = port_options[0] if len(port_options) else None

        if portname:
            with mido.open_input(portname) as midi_port:
                print("Device connected: {}".format(portname))
                thread_device = threading.Thread(target=thread_device_input, daemon=True, args=(midi_port,))
                thread_device.start()
                while ALIVE and portname in mido.get_input_names():
                    wait_for_usb_change()
                thread_device.join(1)
                print("Device disconnected: {}".format(portname))
        else:
            print("No Midi Device Detected")
        if ALIVE:
            wait_for_usb_change()


def thread_play_midi_file(filename):
    global ALIVE
    global HALT_PLAYBACK

    available_songs = [x.replace(".mid", "") for x in os.listdir("../midi_songs")]
    best_match = difflib.get_close_matches(filename, available_songs, n=1, cutoff=0.1)
    if len(best_match):
        best_match = best_match[0]
    else:
        print("Couldn't find matching midi file for \"{}\"".format(filename))
        return

    midifile = mido.MidiFile("../midi_songs/{}.mid".format(best_match))
    midifile.ticks_per_beat *= config.playback_speed

    print("Playing file: {}".format(best_match))
    print("Expected play time: {:.2f}".format(midifile.length * config.playback_speed))
    for i, track in enumerate(midifile.tracks):
        print('Track {}: {}'.format(i, track.name))

    for msg in midifile.play(meta_messages=True):
        handle_midi_event(msg)
        if not ALIVE or HALT_PLAYBACK:
            print("Halting midi playback!")
            HALT_PLAYBACK = False
            break

    # stop all patterns
    leds.cmd_queue.put("clear")


def thread_midi_server(port):
    global ALIVE
    print("Starting midi_server ({}:{})".format(MY_IP, port))
    with PortServer('localhost', port) as server:
        while True:
            client = server.accept()
            try:
                for message in client:
                    handle_midi_event(message)
                    if not ALIVE:
                        print("Closing midi_server")
                        return
            except:
                print("Remote Client Disconnected")


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        global HALT_PLAYBACK

        data = str(self.request.recv(1024), 'ascii').strip()
        if re.findall("^play:", data):
            thread_playback = threading.Thread(target=thread_play_midi_file, daemon=True, args=(data[5:].strip(),))
            thread_playback.start()
        elif re.findall("^stop", data):
            HALT_PLAYBACK = True
        elif re.findall("^pat:", data):
            leds.cmd_queue.put(data[4:].strip())
        elif re.findall("^vol:|^volume:", data):
            config.playback_volume = float(data[data.find(":") + 1])
        elif re.findall("^spd:|^speed:", data):
            config.playback_speed = float(data[data.find(":") + 1])

        # response = bytes("{}: {}".format(cur_thread.name, data), 'ascii')
        # self.request.sendall(response)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def process_update_leds():
    global ALIVE
    global leds
    print("Starting led_update_loop")
    while ALIVE:
        while not leds.cmd_queue.empty():
            leds.text_cmd(leds.cmd_queue.get())
        while not leds.midi_queue.empty():
            msg = leds.midi_queue.get()
            msg.note = bells.map_note(msg.note)
            leds.event(msg)
        leds.step()
        sleep(1.0 / 100)
    leds.close()


# /////////////////////////// MAIN ///////////////////////////
def main():
    # mp.set_start_method('spawn')
    process_leds = mp.Process(target=process_update_leds)
    process_leds.start()

    thread_device = threading.Thread(target=thread_device_monitor, daemon=True)
    thread_device.start()
    thread_midi = threading.Thread(target=thread_midi_server, daemon=True, args=(9080,))
    thread_midi.start()

    cmd_server = ThreadedTCPServer(("localhost", 9081), ThreadedTCPRequestHandler)
    thread_cmd_server = threading.Thread(target=cmd_server.serve_forever, daemon=True)
    print("Starting cmd_server ( {}:{} )".format(MY_IP, 9081))
    thread_cmd_server.start()

    # detect OS and load gpio pedals if on raspberry pi
    if IS_RASPBERRY:
        from gpiozero import Button
        damp_pedal = Button("GPIO17")
        mort_pedal = Button("GPIO27")
        damp_pedal.when_pressed = bells.pedal_sustain_on
        damp_pedal.when_released = bells.pedal_sustain_off
        mort_pedal.when_pressed = bells.pedal_mortello_on
        mort_pedal.when_released = bells.pedal_mortello_off

    # thread_leds.join()
    process_leds.join()
    bells.close()
    cmd_server.server_close()
    cmd_server.shutdown()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigint_handler)
    main()
