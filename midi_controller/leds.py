import importlib
from led_patches.base import State
import os
import numpy as np
import re
import ctypes


# detect and load patches
patch_files = [f.replace(".py", "") for f in os.listdir("led_patches") if (os.path.isfile(os.path.join("led_patches", f)) and f.endswith(".py"))]
patch_classes = {}
print("Importing Patches:")
for name in patch_files:
    print("    - %s" % name)
    globals()[name] = importlib.import_module("led_patches." + name, package=None)
    patch_classes[name] = globals()[name].__dict__[name]

# detect OS and load visualization istead of hardware when on PC
os_type = " ".join(os.uname())
print("Current OS: %s" % os_type)
IS_RASPBERRY = "raspberrypi" in os_type or "arm" in os_type
if IS_RASPBERRY:
    print("Loading on Raspberry pi, using pwm hardware.")
    from ledlib.neopixel import Adafruit_NeoPixel
    import ledlib._rpi_ws281x as ws
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

        # allocate new array
        self.raw_buffer = (ctypes.c_uint8 * self.length * 4)()
        # ws.ws2811_channel_t_leds_set(self._hw._channel, ctypes.byref(self.raw_buffer))
        ws.set_buffer(self._hw._channel, ctypes.byref(self.raw_buffer))

    def flush(self):
        """ Flush buffer to strip
        """
        buf = np.minimum(np.maximum(np.array(self.buffer * 255, np.uint32), 0), 255)
        packed_buf = (buf[:, 0] << 16) + (buf[:, 1] << 8) + buf[:, 2]
        # for x in range(self.length):
            # self._hw._led_data[x] = int(packed_buf[x])



        ctypes.memmove(ctypes.byref(self.raw_buffer), packed_buf.tobytes(), self.length * 4)

        self._hw.show()

    def __getitem__(self, idx):
        return self.buffer[idx]

    def __setitem__(self, idx, value):
        self.buffer[idx] = value


class LightController(object):
    """  Manage active led Patches """
    def __init__(self, config):
        super(LightController, self).__init__()
        self.config = config
        self.leds = LedInterface(
            np.array(config["Leds"]["note_array"]).size * config["Leds"]["leds_per_note"],
            config["Leds"]["pin"],
            config["Leds"]["dma"],
            config["Leds"]["channel"]
        )
        self.active_pats = []
        self.default_off_pat = patch_classes["fade"](self.config)

    def close(self):
        if hasattr(self.leds._hw, "close"):
            self.leds._hw.close()

    def print_active_pats(self):
        print("---- Active Patterns ----")
        print("\n".join(["{:40} {:10}".format(each.__class__.__name__, each.state) for each in self.active_pats]))
        print("-------------------------")

    def step(self):
        """ tick update """
        if len(self.active_pats):
            for each in self.active_pats:
                if each.state == State.OFF:
                    self.active_pats.remove(each)
                elif each.state.value > State.OFF.value:
                    each.step(self.leds)
        else:
            # if no active pats, run default "off" patch
            self.default_off_pat.step(self.leds)
        self.leds.flush()

    def event(self, event):
        """ handle midi event """
        for each in self.active_pats:
            each.event(event)

    def stop_patch(self, name):
        """ stop an active patch """
        for each in self.active_pats:
            if name == each.__class__.__name__:
                each.state = State.STOP

    def start_patch(self, name, solo=False, **kwargs):
        """ start a patch, stop all others """
        if name in patch_classes.keys():
            # start the desired patch (no duplicates)
            self.active_pats.append(patch_classes[name](self.config, **kwargs))
            if solo:
                # stop all other patches
                for each in self.active_pats:
                    if name != each.__class__.__name__:
                        each.state = State.STOP
        else:
            print("Unknown patch \"{}\"".fromat(name))

    def text_cmd(self, cmd):
        """ parse and execute pattern commands from strings """
        re_range = re.compile("([a-z0-9#]+):([a-z0-9#]+)")
        re_color = re.compile("\(\s*([\d]+)\s*,?\s*([\d]+)\s*,?\s*([\d]+)\s*\)")
        #re_args = re.compile("[^()\s][\w:]+|\([\w\s\.,]+\)")
        re_number = re.compile("(?:\s+|^)([\d.]+)(?:\s+|$)")
        re_pats = re.compile("|".join(("^" + x) for x in patch_classes.keys()))

        colors = {
            "red": "(255, 0, 0)",
            "green": "(0, 255, 0)",
            "blue": "(0, 0, 255)",
            "orange": "(255, 128, 0)",
            "yellow": "(255, 255, 0)",
            "purple": "(255, 0, 255)",
            "cyan": "(0, 255, 255)",
            "black": "(0, 0, 0)",
            "off": "(0, 0, 0)",
        }

        for line in cmd.lower().split(";"):
            line = line.strip()

            if line.startswith("clear"):
                # stop all patches
                for each in self.active_pats:
                    each.state = State.STOP

            else:
                # parse patch with args
                patch_match = re_pats.findall(line)
                if len(patch_match):
                    patch_name = patch_match[0]
                    # print("patch_name: {}".format(patch_name))

                    # handle args
                    kwargs = {}

                    # get colors
                    for color, value in colors.items():
                        line = line.replace(color, value)
                    kwargs["colors"] = np.array(re_color.findall(line)).astype(np.float) / 255.0

                    # misc flags
                    kwargs["hold"] = "hold" in line
                    kwargs["random"] = "random" in line
                    kwargs["rainbow"] = "rainbow" in line
                    kwargs["all"] = "all" in line

                    # free numbers (rate)
                    m_number = re_number.findall(line)
                    if len(m_number):
                        kwargs["rate"] = m_number[0]

                    # note range
                    m_range = re_range.findall(line)
                    if len(m_range):
                        kwargs["range"] = tuple(self.config.t2m[each] - self.config["Bells"]["midi_offset"] for each in m_range[0])

                    try:
                        self.start_patch(patch_name, **kwargs)
                    except:
                        print("Error: Failed to start patch \"{}\"\nWith args: {}".format(patch_name, str(kwargs)))
                else:
                    print("No valid LED patch found in \"{}\"".format(line))

        self.print_active_pats()
