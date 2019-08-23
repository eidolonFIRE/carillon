from led_patches.base import base, State, color_wheel
import numpy as np
from random import random
from time import time


class spin(base):
    def __init__(self, layout, **kwargs):
        super(spin, self).__init__(layout, kwargs)
        self.colors = kwargs.get("colors", [])
        self.rainbow = kwargs.get("rainbow", False)
        self.random = kwargs.get("random", False)
        self.rate = kwargs.get("rate", 0.1) * 10
        if not len(self.colors) and not self.random:
            self.colors = np.array([(1, 1, 1)])
        if self.rainbow:
            self.colors = np.array([(1, 0, 0), (0, 1, 0), (0, 0, 1)])
        self.active_notes = {}
        self.last_color = {}
        self.color_index = 0

    def set_led(self, idx, color, leds):
        

        if len(self.colors) == 3:
            leds[idx] *= 0
            leds[idx + 1] *= 0
            leds[idx + 2] *= 0
            for x in range(3):
                sweep = (time() * self.rate + x / 3.0) % 1.0
                leds[idx] += self.colors[x] * (1.0 - min(abs(min(1, sweep * 3)), abs(min(1, (sweep - 1.0) * 3))))
                leds[idx + 1] += self.colors[x] * (1.0 - abs(min(1, (sweep - 0.33333) * 3)))
                leds[idx + 2] += self.colors[x] * max(0, (1.0 - abs(min(1, (sweep - 0.66666) * 3))))
        else:
            sweep = (time() * self.rate) % 1.0
            leds[idx] = self.colors[0] * (1.0 - min(abs(min(1, sweep * 3)), abs(min(1, (sweep - 1.0) * 3))))
            leds[idx + 1] = self.colors[0] * (1.0 - abs(min(1, (sweep - 0.33333) * 3)))
            leds[idx + 2] = self.colors[0] * max(0, (1.0 - abs(min(1, (sweep - 0.66666) * 3))))


    def get_next_color(self):
        if self.random:
            return color_wheel(random())
        else:
            color = self.colors[self.color_index]
            self.color_index += 1
            if self.color_index >= len(self.colors):
                self.color_index = 0
            return color

    def _step(self, state, leds):
        # handle events
        if len(self.events):
            event = self.events.pop()
            if event.type == "note_on" and event.velocity > 0:
                self.active_notes[event.note] = True
                i = self.lut.n2i[event.note]
                color = self.get_next_color()
                self.set_led(i, color, leds)
                self.last_color[i] = color
            elif event.type == "note_on" and event.velocity == 0 or event.type == "note_off":
                self.active_notes[event.note] = False

        # hold value while note active
        for note, value in self.active_notes.items():
            if value:
                i = self.lut.n2i[note]
                self.set_led(i, self.last_color[i], leds)

        if state == State.START:
            return State.RUNNING
        if state == State.STOP:
            return State.OFF
