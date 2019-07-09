import numpy as np
import json


class Config(object):
    """ LED layout configurations """
    def __init__(self, config_filename):
        """  Config  """
        self._config_file = json.load(open(config_filename, 'r'))
        self.notes_matrix = np.array(self._config_file["Leds"]["note_array"])
        self.leds_per_note = int(self._config_file["Leds"]["leds_per_note"])

        """  LUTS  """
        self.len = self.notes_matrix.size * self.leds_per_note
        # Note to Index
        self.n2i = [0] * self.notes_matrix.size
        # Index to Note
        self.i2n = [0] * self.len
        # Note to coordinate position
        self.n2p = [0] * self.notes_matrix.size
        # Position to Note
        self.p2n = {}
        # text to midi note
        self.t2m = {}
        self._note_list = [
            ["c", 12],
            ["c#", 13],
            ["db", 13],
            ["d", 14],
            ["d#", 15],
            ["eb", 15],
            ["e", 16],
            ["f", 17],
            ["f#", 18],
            ["gb", 18],
            ["g", 19],
            ["g#", 20],
            ["ab", 20],
            ["a", 21],
            ["a#", 22],
            ["bb", 22],
            ["b", 23],
        ]

        self._build_LUTs()

    def __getitem__(self, key):
        """ access the json config directly """
        return self._config_file[key]

    def _build_LUTs(self):
        self.w = self.notes_matrix.shape[0]
        self.h = self.notes_matrix.shape[1]
        for x in range(self.w):
            for y in range(self.h):
                note = self.notes_matrix[x, y]
                index = y * self.leds_per_note + x * self.h * self.leds_per_note
                self.n2i[note] = index
                self.i2n[index + 0] = note
                self.i2n[index + 1] = note
                self.i2n[index + 2] = note
                self.n2p[note] = (x, y)
                self.p2n[(x, y)] = note

        # text to midi note
        for octave in range(8):
            for text, note in self._note_list:
                self.t2m[text + str(octave)] = note + 12 * octave
