from led_patches.base import base, State
from random import shuffle
import numpy as np


class off(base):
    def __init__(self, layout, **kwargs):
        self.strip_order = list(range(layout.len))
        super(off, self).__init__(layout, kwargs)
        shuffle(self.strip_order)
        self.i = 0

    def _step(self, state, leds):
        if self.i >= self.len:
            self.i = 0
            shuffle(self.strip_order)
        leds[self.strip_order[self.i]] = np.zeros((3))
        self.i += 1

        if state == State.START:
            return State.RUNNING
        elif state == State.STOP:
            return State.OFF
