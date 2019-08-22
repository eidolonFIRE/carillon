from led_patches.base import base, State, color_blend
import numpy as np


class note_pulse_gradient(base):
    def __init__(self, layout, **kwargs):
        super(note_pulse_gradient, self).__init__(layout, kwargs)
        self.high_color = np.array(kwargs.get("high_color", (0.0, 0.0, 1.0)))
        self.low_color = np.array(kwargs.get("low_color", (1.0, 0.0, 0.0)))
        self.active_notes = {}

    def set_led(self, note, vel, leds):
        color = color_blend(self.low_color, self.high_color, float(note) / self.lut.notes_matrix.size)

        # set LEDs
        idx = self.lut.n2i[note]
        leds[idx] = color
        leds[idx + 1] = color
        leds[idx + 2] = color

    def _step(self, state, leds):
        # handle events
        if len(self.events):
            event = self.events.pop()
            if event.type == "note_on" and event.velocity > 0:
                self.active_notes[event.note] = event.velocity
                self.set_led(event.note, event.velocity, leds)
            elif event.type == "note_on" and event.velocity == 0 or event.type == "note_off":
                self.active_notes[event.note] = event.velocity

        # hold value while note active
        if self.hold:
            for note, value in self.active_notes.items():
                if value:
                    self.set_led(note, value, leds)

        if state == State.START:
            return State.RUNNING
        if state == State.STOP:
            return State.OFF
