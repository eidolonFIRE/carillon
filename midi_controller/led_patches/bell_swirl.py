from led_patches.base import base, State, color_blend
from random import shuffle


class bell_swirl(base):
    def __init__(self, layout, **kwargs):
        super(bell_swirl, self).__init__(layout)
        self.order = list(range(self.lut.notes_matrix.size))
        shuffle(self.order)
        self.idx = 0

    def _step(self, state, leds):
        for each in range(3):
            i = self.order[self.idx] * 3
            temp = leds[i + 2]
            leds[i + 2] = color_blend(leds[i + 2], leds[i + 1], 0.1)
            leds[i + 1] = color_blend(leds[i + 1], leds[i + 0], 0.1)
            leds[i + 0] = color_blend(leds[i + 0], temp, 0.1)

            self.idx += 1
            if self.idx >= len(self.order):
                self.idx = 0

        if state == State.START:
            return State.RUNNING
        if state == State.STOP:
            return State.OFF
