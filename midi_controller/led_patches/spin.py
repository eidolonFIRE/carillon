from led_patches.base import base, State
import numpy as np


class spin(base):
    def __init__(self, layout, **kwargs):
        super(spin, self).__init__(layout, kwargs)
        self.colors = kwargs.get("colors", [])
        self.rainbow = kwargs.get("rainbow", False)
        self.rate = kwargs.get("rate", 0.1) * 10
        if len(self.colors) < 3 or self.rainbow:
            self.colors = np.array([(1, 0, 0), (0, 1, 0), (0, 0, 1)])
        self.active_notes = {}
        self.spin_pos = {}

    def set_led(self, idx, leds):
        leds[idx] *= 0
        leds[idx + 1] *= 0
        leds[idx + 2] *= 0
        for x in range(3):
            sweep = (self.spin_pos[idx] * self.rate + x / 3.0) % 1.0
            leds[idx] += self.colors[x] * (1.0 - min(abs(min(1, sweep * 3)), abs(min(1, (sweep - 1.0) * 3))))
            leds[idx + 1] += self.colors[x] * (1.0 - abs(min(1, (sweep - 0.33333) * 3)))
            leds[idx + 2] += self.colors[x] * max(0, (1.0 - abs(min(1, (sweep - 0.66666) * 3))))
        self.spin_pos[idx] *= 0.995

    def _step(self, state, leds):
        # handle events
        if len(self.events):
            event = self.events.pop()
            if event.type == "note_on" and event.velocity > 0:
                self.active_notes[event.note] = True
                i = self.lut.n2i[event.note]
                self.spin_pos[i] = 5 * event.velocity / 127.0 + 1
                self.set_led(i, leds)
            elif event.type == "note_on" and event.velocity == 0 or event.type == "note_off":
                self.active_notes[event.note] = False

        # hold value while note active
        for note, value in self.active_notes.items():
            if value:
                i = self.lut.n2i[note]
                self.set_led(i, leds)

        if state == State.START:
            return State.RUNNING
        if state == State.STOP:
            return State.OFF
