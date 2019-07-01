from led_patches.base import base, State, color_wheel, color_blend
from time import time


class fade_to_rainbow(base):
    def __init__(self, layout):
        super(fade_to_rainbow, self).__init__(layout)

    def _step(self, state, leds):
        for idx in range(self.lut.len):
            leds[idx] = color_blend(leds[idx], color_wheel(float(idx) / 150.0 + time() / 40.0), 0.99)

        if state == State.START:
            return State.RUNNING
        if state == State.STOP:
            return State.OFF
