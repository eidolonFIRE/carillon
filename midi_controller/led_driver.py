import os
import numpy as np


# detect OS and load visualization istead of hardware when on PC
os_type = " ".join(os.uname())
print("Current OS: %s" % os_type)
if "raspberrypi" in os_type:
    print("Loading on Raspberry pi, using pwm hardware.")
    from ledlib.neopixel import Adafruit_NeoPixel, ws
else:
    print("Loading on dev PC, using stub visualization.")
    from led_stub import Adafruit_NeoPixel_stub as Adafruit_NeoPixel, ws


###############################################################################


def to_color(red=0.0, green=0.0, blue=0.0):
    return np.array([red, green, blue])


def color_blend(A, B, ratio=0.5):
    """ Weighted average of two colors.
        Note: non luminous preserving!
    """
    return A * ratio + (1.0 - ratio) * B


def color_wheel(pos, bri=1.0):
    """ Select color from rainbow
    """
    pos = pos % 1.0
    if pos < 0.333333:
        return np.array([pos * 3.0 * bri, (1.0 - pos * 3.0) * bri, 0.0])
    elif pos < 0.666667:
        pos -= 0.333333
        return np.array([(1.0 - pos * 3.0) * bri, 0.0, pos * 3.0 * bri])
    else:
        pos -= 0.666667
        return np.array([0.0, pos * 3.0 * bri, (1.0 - pos * 3.0) * bri])


def color_to_int(color):
    temp = color * 255.0
    return (
        (max(0, min(255, int(temp[0]))) << 16) |
        (max(0, min(255, int(temp[1]))) << 8) |
        (max(0, min(255, int(temp[2])))))


###############################################################################


class LedInterface(object):
    """ Hardware interface
    """
    def __init__(self, length, pin, dma, channel):
        super(LedInterface, self).__init__()
        self._hw = Adafruit_NeoPixel(length, pin=pin, dma=dma, channel=channel, strip_type=ws.WS2811_STRIP_GRB)
        self._hw.begin()
        self.length = length
        self.buffer = np.zeros((length, 3))

    def flush(self):
        """ Flush buffer to strip
        """
        for x in range(self.length):
            self._hw._led_data[x] = color_to_int(self.buffer[x])
        self._hw.show()

    def __getitem__(self, idx):
        return self.buffer[idx]

    def __setitem__(self, idx, value):
        self.buffer[idx] = value
