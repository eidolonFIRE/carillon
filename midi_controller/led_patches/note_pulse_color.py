from led_patches.base import base, State
import numpy as np


class note_pulse_color(base):
    def __init__(self, layout, **kwargs):
        super(note_pulse_color, self).__init__(layout, kwargs)
        self.color = np.array(kwargs.get("color", (1.0, 1.0, 1.0)))
        self.hold = kwargs.get("hold", False)
        self.active_notes = {}

    def set_led(self, idx, leds):
        leds[idx] = self.color
        if not self.one_led:
            leds[idx + 1] = self.color
            leds[idx + 2] = self.color

    def _step(self, state, leds):
        # handle events
        if len(self.events):
            event = self.events.pop()
            if event.type == "note_on" and event.velocity > 0:
                self.active_notes[event.note] = True
                i = self.lut.n2i[event.note]
                self.set_led(i, leds)
            elif event.type == "note_on" and event.velocity == 0 or event.type == "note_off":
                self.active_notes[event.note] = False

        # hold value while note active
        if self.hold:
            for note, value in self.active_notes.items():
                if value:
                    i = self.lut.n2i[note]
                    self.set_led(i, leds)

        if state == State.START:
            return State.RUNNING
        if state == State.STOP:
            return State.OFF
