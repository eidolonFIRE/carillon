from led_patches.base import base, State, color_wheel, color_blend
from time import time


class fade_to_rainbow(base):
    def __init__(self, layout, **kwargs):
        super(fade_to_rainbow, self).__init__(layout, kwargs)
        self.rate = float(kwargs.get("rate", 0.95))

    def _step(self, state, leds):
        for idx in range(self.lut.len):
            if self.range[0] <= self.lut.i2n[idx] <= self.range[1]:
                leds[idx] = color_blend(leds[idx], color_wheel(float(idx) / 150.0 + time() / 40.0), self.rate)

        if state == State.START:
            return State.RUNNING
        if state == State.STOP:
            return State.OFF
