from led_patches.base import base, State, color_blend, color_wheel
import numpy as np
from time import time


class fade(base):
    def __init__(self, layout, **kwargs):
        super(fade, self).__init__(layout, kwargs)
        self.color = np.array(kwargs.get("color", (0, 0, 0)))
        self.rainbow = kwargs.get("rainbow", False)
        self.rate = float(kwargs.get("rate", 0.95))

    def _step(self, state, leds):
        for idx in range(self.lut.len):
            if self.range[0] <= self.lut.i2n[idx] <= self.range[1]:
                leds[idx] = color_blend(leds[idx], color_wheel(float(idx) / 150.0 + time() / 40.0) if self.rainbow else self.color, self.rate)

        if state == State.START:
            return State.RUNNING
        if state == State.STOP:
            return State.OFF
