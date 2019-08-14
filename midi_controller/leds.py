import importlib
from led_patches.base import State
import os
import numpy as np
import re


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
        self.default_off_pat = patch_classes["off"](self.config)

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
            print("Unknown patch \"%s\"" % name)

    def text_cmd(self, cmd):
        """ parse and execute pattern commands from strings """
        re_name = "\s*([\w_]+)"
        re_args = "([\w_]+)=([\w_:\(\)\.,]+)"
        re_note = "([a-z0-9#]+):([a-z0-9#]+)"
        re_color = "\(([0-9\.]+),([0-9\.]+),([0-9\.]+)\)"
        re_true = "(true|yes|)"

        cmd = cmd.lower()

        if re.findall("^add", cmd):
            cmd = cmd[3:]
            # start a pattern
            name = re.findall(re_name, cmd)
            args = re.findall(re_args, cmd)
            if len(name):
                if name[0] in patch_classes.keys():
                    # handle args
                    kwargs = {}
                    for key, value in args:
                        try:
                            if key == "range":
                                kwargs[key] = tuple(self.config.t2m[each] - self.config["Bells"]["midi_offset"] for each in re.findall(re_note, value)[0])
                            elif key == "hold":
                                kwargs[key] = bool(re.match(re_true, value))
                            elif key == "one_led":
                                kwargs[key] = bool(re.match(re_true, value))
                            elif key == "color":
                                kwargs[key] = tuple(float(x) for x in re.findall(re_color, value)[0])
                            elif key == "rate":
                                kwargs[key] = float(value)
                            else:
                                print("Error: Unknown pattern \"{}\"".format(key))
                        except:
                            print("Error: failed to parse \"{}={}\"".format(key, value))

                    self.start_patch(name[0], **kwargs)
                else:
                    print("Error: Unrecognized patch \"{}\"".format(name[0]))

        elif re.findall("^rem", cmd):
            cmd = cmd[3:]
            # stop a pattern
            name = re.findall(re_name, cmd)
            if len(name):
                if name[0] in patch_classes.keys():
                    self.stop_patch(name[0])
                else:
                    print("Error: Unrecognized patch \"{}\"".format(name[0]))

        elif re.findall("^clear", cmd):
            # stop all patterns
            for each in self.active_pats:
                each.state = State.STOP

        else:
            print("Error: Unable to parse command \"{}\"".format(cmd))

        self.print_active_pats()
