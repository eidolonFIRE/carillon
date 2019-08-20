from led_patches.base import base, State, color_wheel
from random import random


class note_pulse_random(base):
    def __init__(self, layout, **kwargs):
        super(note_pulse_random, self).__init__(layout, kwargs)
        self.hold = kwargs.get("hold", False)
        self.active_notes = {}
        self._note_colors = {}

    def set_led(self, note, color, leds):

        # set LEDs
        idx = self.lut.n2i[note]
        leds[idx] = color
        if not self.one_led:
            leds[idx + 1] = color
            leds[idx + 2] = color

    def _step(self, state, leds):
        # handle events
        if len(self.events):
            event = self.events.pop()
            if event.type == "note_on" and event.velocity > 0:
                self.active_notes[event.note] = event.velocity
                color = color_wheel(random())
                self._note_colors[event.note] = color
                self.set_led(event.note, color, leds)
            elif event.type == "note_on" and event.velocity == 0 or event.type == "note_off":
                self.active_notes[event.note] = event.velocity

        # hold value while note active
        if self.hold:
            for note, value in self.active_notes.items():
                if value:
                    self.set_led(note, self._note_colors.get(note, (0, 0, 0)), leds)

        if state == State.START:
            return State.RUNNING
        if state == State.STOP:
            return State.OFF
