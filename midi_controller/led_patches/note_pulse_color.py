from led_patches.base import base, State
import numpy as np


class note_pulse_color(base):
    def __init__(self, layout, **kwargs):
        super(note_pulse_color, self).__init__(layout)
        if "color" in kwargs:
            self.color = np.array(kwargs["color"])
        else:
            self.color = np.array((1.0, 1.0, 1.0))
        if "one_led" in kwargs:
            self.one_led = kwargs["one_led"]

    def _step(self, state, leds):
        if len(self.events):
            event = self.events.pop()
            # print(event)
            if event.type == "note_on":

                i = self.lut.n2i[event.note]

                leds[i + 0] = self.color
                if not self.one_led:
                    leds[i + 1] = self.color
                    leds[i + 2] = self.color

        if state == State.START:
            return State.RUNNING
        if state == State.STOP:
            return State.OFF
