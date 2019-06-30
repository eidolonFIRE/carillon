from led_patches.base import base, State
import numpy as np


class note_pulse(base):
    def __init__(self, layout):
        super(note_pulse, self).__init__(layout)

    def _step(self, state, leds):
        if len(self.events):
            event = self.events.pop()
            # print(event)
            if event.type == "note_on":

                i = self.lut.n2i[event.note]

                leds[i + 0] = np.array((1.0, 0.0, 0.0)) * event.velocity / 127.0
                leds[i + 1] = np.array((0.0, 1.0, 0.0)) * event.velocity / 127.0
                leds[i + 2] = np.array((0.0, 0.0, 1.0)) * event.velocity / 127.0
            elif event.type == "note_off":
                i = self.lut.n2i[event.note]
                leds[i + 0] = np.zeros((3))
                leds[i + 1] = np.zeros((3))
                leds[i + 2] = np.zeros((3))

        if state == State.START:
            return State.RUNNING

        if state == State.STOP:
            return State.OFF
