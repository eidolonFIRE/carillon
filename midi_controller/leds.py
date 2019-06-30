import importlib
from led_patches.base import State
import os
import numpy as np


# detect and load patches
patch_files = [f.replace(".py", "") for f in os.listdir("led_patches") if os.path.isfile(os.path.join("led_patches", f))]
patch_classes = {}
print("Importing Patches:")
for name in patch_files:
    print("    - %s" % name)
    globals()[name] = importlib.import_module("led_patches." + name, package=None)
    patch_classes[name] = globals()[name].__dict__[name]

# detect OS and load visualization istead of hardware when on PC
os_type = " ".join(os.uname())
print("Current OS: %s" % os_type)
if "raspberrypi" in os_type or "arm" in os_type:
    print("Loading on Raspberry pi, using pwm hardware.")
    from ledlib.neopixel import Adafruit_NeoPixel, ws
else:
    print("Loading on dev PC, using pygame visualization.")
    from led_viz import Adafruit_NeoPixel_viz as Adafruit_NeoPixel, ws


class LedInterface(object):
    """ Hardware interface
    """
    def __init__(self, length, pin, dma, channel):
        super(LedInterface, self).__init__()
        self._hw = Adafruit_NeoPixel(length, pin=pin, dma=dma, channel=channel, strip_type=ws.WS2811_STRIP_GRB)
        self._hw.begin()
        self.length = length
        self.buffer = np.zeros((length, 3))

    @staticmethod
    def color_to_int(color):
        temp = color * 255.0
        return (
            (max(0, min(255, int(temp[0]))) << 16) |
            (max(0, min(255, int(temp[1]))) << 8) |
            (max(0, min(255, int(temp[2])))))

    def flush(self):
        """ Flush buffer to strip
        """
        for x in range(self.length):
            self._hw._led_data[x] = LedInterface.color_to_int(self.buffer[x])
        self._hw.show()

    def __getitem__(self, idx):
        return self.buffer[idx]

    def __setitem__(self, idx, value):
        self.buffer[idx] = value


class LedLayout(object):
    """ LED layout configurations """
    def __init__(self, config):
        """  Config  """
        self.notes_matrix = np.array(config["note_array"])
        self.leds_per_note = int(config["leds_per_note"])

        """  LUTS  """
        self.len = self.notes_matrix.size * self.leds_per_note
        # Note to Index
        self.n2i = [0] * self.notes_matrix.size
        # Index to Note
        self.i2n = [0] * self.len
        # Note to coordinate position
        self.n2p = [0] * self.notes_matrix.size
        # Position to Note
        self.p2n = {}

        self._build_LUTs()

    def _build_LUTs(self):
        self.w = self.notes_matrix.shape[0]
        self.h = self.notes_matrix.shape[1]
        for x in range(self.w):
            for y in range(self.h):
                note = self.notes_matrix[x, y]
                index = y * self.leds_per_note + x * self.h * self.leds_per_note
                self.n2i[note] = index
                self.i2n[index + 0] = note
                self.i2n[index + 1] = note
                self.i2n[index + 2] = note
                self.n2p[note] = (x, y)
                self.p2n[(x, y)] = note


class LightController(object):
    """  Manage active led Patches """
    def __init__(self, config):
        super(LightController, self).__init__()
        self.leds = LedInterface(
            np.array(config["note_array"]).size * config["leds_per_note"],
            config["pin"],
            config["dma"],
            config["channel"]
        )
        self.layout = LedLayout(config)
        self.active_pats = []

    def step(self):
        for each in self.active_pats:
            if each.state == State.OFF:
                self.active_pats.remove(each)
            elif each.state.value > State.OFF.value:
                each.step(self.leds)
        self.leds.flush()

    def event(self, event):
        for each in self.active_pats:
            each.event(event)

    def start_patch(self, name, solo=True):
        ''' start a patch, stop all others '''
        if name in patch_classes.keys():
            for each in self.active_pats:
                if each.__class__.__name__ == name:
                    # patch already running!
                    return
            # start the desired patch (no duplicates)
            self.active_pats.append(patch_classes[name](self.layout))
            if solo and not self.active_pats[-1].is_oneshot:
                # stop all other patches
                for each in self.active_pats:
                    if name != each.__class__.__name__:
                        each.state = State.STOP
        else:
            print("Unknown patch \"%s\"" % name)
