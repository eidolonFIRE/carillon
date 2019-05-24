from enum import Enum
import pygame

pygame.init()
myDisplay = pygame.display.set_mode((700, 900), pygame.RESIZABLE)
pygame.display.set_caption('Charity Tree Viz')

myDisplay.fill((10, 10, 10))
pygame.display.update()


class ws(Enum):
    WS2811_STRIP_GRB = 0


class Adafruit_NeoPixel_viz(object):
    """Pygame visualizer for led strip"""
    def __init__(self, length, pin, dma, channel, strip_type):
        super(Adafruit_NeoPixel_viz, self).__init__()
        self.length = length
        self.pin = pin
        self.dma = dma
        self.channel = channel
        self.strip_type = strip_type
        self._led_data = [0] * length

    def begin(self):
        myDisplay.fill((10, 10, 10))

    @staticmethod
    def color_to_tuple(color):
        return (color >> 16, (color >> 8) & 0xff, color & 0xff)

    def show(self):
        for index, each in enumerate(self._led_data):
            pos = ((index % 9) * 15 + 20, (index / 9) * 40 + 20, 5, 10)
            pygame.draw.rect(myDisplay, Adafruit_NeoPixel_viz.color_to_tuple(each), pos)
        pygame.display.update()

    def setPixelColor(self, index, color):
        self._led_data[index] = color
