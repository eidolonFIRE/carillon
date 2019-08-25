from led_patches.base import base, State, color_wheel
import numpy as np
from time import time


class fade(base):
    def __init__(self, layout, **kwargs):
        super(fade, self).__init__(layout, kwargs)
        colors = kwargs.get("colors", [])
        if len(colors):
            self.color = colors[0]
        else:
            self.color = np.array((0, 0, 0))
        self.rainbow = kwargs.get("rainbow", False)
        self.rate = float(kwargs.get("rate", 0.05))

    def _step(self, state, leds):
        # empty queue
        self.events.clear()

        # fade colors
        target_color = color_wheel(time() / 30.0) if self.rainbow else self.color
        leds.buffer = leds.buffer * (1.0 - self.rate) + self.rate * target_color

        if state == State.START:
            return State.RUNNING
        if state == State.STOP:
            return State.OFF
