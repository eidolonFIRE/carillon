from led_patches.base import base, State, color_wheel
import numpy as np
from random import random
from time import time


class simple(base):
    def __init__(self, layout, **kwargs):
        super(simple, self).__init__(layout, kwargs)
        self.colors = kwargs.get("colors", [])
        self.rainbow = kwargs.get("rainbow", False)
        self.random = kwargs.get("random", False)
        self.all = kwargs.get("all", False)
        if not len(self.colors) and not self.random:
            self.colors = np.array([(0, 0, 0)])
        self.active_notes = {}
        self.last_color = {}
        self.color_index = 0

    def set_led(self, idx, color, leds):
        if self.all:
            leds[:] = color
        else:
            leds[idx] = color
            leds[idx + 1] = color
            leds[idx + 2] = color

    def get_next_color(self):
        if self.rainbow:
            return color_wheel(time() / 20)
        elif self.random:
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
        if self.hold:
            for note, value in self.active_notes.items():
                if value:
                    i = self.lut.n2i[note]
                    self.set_led(i, self.last_color[i], leds)

        if state == State.START:
            return State.RUNNING
        if state == State.STOP:
            return State.OFF
