from led_patches.base import base, State
import math
from random import random
import numpy as np


class gradient(base):
    def __init__(self, layout, **kwargs):
        super(gradient, self).__init__(layout, kwargs)
        self.colors = kwargs.get("colors", [])
        if not len(self.colors):
            # if no colors provided, make shit up
            self.colors = np.array(((1, 0, 0), (0, 0, 1)))
        elif len(self.colors) < 2:
            # if only one color provided, duplicate it
            self.colors = [self.colors[0], self.colors[1]]
        self.all = kwargs.get("all", False)
        self.random = kwargs.get("random", False)
        self.active_notes = {}
        self.last_color = {}

    def set_led(self, note, color, leds):
        if self.all:
            leds[:] = color
        else:
            idx = self.lut.n2i[note]
            leds[idx] = color
            leds[idx + 1] = color
            leds[idx + 2] = color

    def get_next_color(self, note):
        # interp value
        if self.random:
            i = random()
        else:
            i = max(0.0, min(1.0, float(note - self.range[0]) / (self.range[1] - self.range[0] - 1)))

        # interpolate colors
        color_i = min(len(self.colors) - 2, math.floor(i * (len(self.colors) - 1)))
        color_a = self.colors[color_i]
        color_b = self.colors[color_i + 1]
        i_rem = i * (len(self.colors) - 1) - color_i
        return color_a * (1.0 - i_rem) + color_b * i_rem

    def _step(self, state, leds):
        # handle events
        for event in self.events:
            if event.type == "note_on" and event.velocity > 0:
                self.active_notes[event.note] = True
                color = self.get_next_color(event.note)
                self.last_color[event.note] = color
                self.set_led(event.note, color, leds)
            elif event.type == "note_on" and event.velocity == 0 or event.type == "note_off":
                self.active_notes[event.note] = False
        self.events.clear()

        # hold value while note active
        if self.hold:
            for note, value in self.active_notes.items():
                if value:
                    self.set_led(note, self.last_color[note], leds)

        if state == State.START:
            return State.RUNNING
        if state == State.STOP:
            return State.OFF
