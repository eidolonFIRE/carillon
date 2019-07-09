from led_patches.base import base, State, color_blend
import numpy as np


class fade_to_color(base):
    def __init__(self, layout, **kwargs):
        super(fade_to_color, self).__init__(layout, kwargs)
        self.color = np.array(kwargs.get("color", (0, 0, 0)))
        self.rate = float(kwargs.get("rate", 0.95))

    def _step(self, state, leds):
        for idx in range(self.lut.len):
            if self.range[0] <= self.lut.i2n[idx] <= self.range[1]:
                leds[idx] = color_blend(leds[idx], self.color, self.rate)

        if state == State.START:
            return State.RUNNING
        if state == State.STOP:
            return State.OFF
