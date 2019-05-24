from enum import Enum
import numpy as np


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
        return np.array((pos * 3.0 * bri, (1.0 - pos * 3.0) * bri, 0.0))
    elif pos < 0.666667:
        pos -= 0.333333
        return np.array(((1.0 - pos * 3.0) * bri, 0.0, pos * 3.0 * bri))
    else:
        pos -= 0.666667
        return np.array((0.0, pos * 3.0 * bri, (1.0 - pos * 3.0) * bri))


class State(Enum):
    UNKNOWN = -1
    OFF = 0
    START = 1
    RUNNING = 2
    STOP = 3
    HARDSTOP = 4


class base(object):
    """  Base LED patch  """
    def __init__(self, layout):
        self.lut = layout
        self.is_oneshot = False
        self.reset()

    def reset(self):
        self.state = State.START
        self.loopCount = 0

    def event(self, note, type, value):
        pass

    def step(self, leds):
        self.loopCount += 1
        self.state = self._step(self.state, leds) or self.state
