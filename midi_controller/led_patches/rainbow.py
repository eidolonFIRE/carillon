from led_patches.base import base, State, color_wheel
from random import shuffle
from time import time


class rainbow(base):
    def __init__(self, layout):
        self.strip_order = list(range(layout.len))
        super(rainbow, self).__init__(layout)

    def reset(self):
        self.i = 0
        shuffle(self.strip_order)

    def _step(self, state, leds):
        for t in range(10):
            if self.i >= self.len:
                self.i = 0
                if state == State.START:
                    return State.RUNNING
            pos = self.strip_order[self.i]
            leds[pos] = color_wheel(float(pos) / 255.0 + time() / 60.0)
            self.i += 1

        if state == State.STOP:
            return State.OFF