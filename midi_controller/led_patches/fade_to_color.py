from led_patches.base import base, State, color_blend
import numpy as np


class fade_to_color(base):
    def __init__(self, layout, **kwargs):
        super(fade_to_color, self).__init__(layout)
        if "color" in kwargs:
            self.color = np.array(kwargs["color"])
        else:
            self.color = np.zeros((3))

    def _step(self, state, leds):
        for idx in range(self.lut.len):
            leds[idx] = color_blend(leds[idx], self.color, 0.99)

        if state == State.START:
            return State.RUNNING
        if state == State.STOP:
            return State.OFF
