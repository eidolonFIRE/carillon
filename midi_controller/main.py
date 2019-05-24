from bells import BellsController
from leds import LightController


# LOAD CONFIG
import json
config = json.load(open('config.json', 'r'))

# Spin up main objects
bells = BellsController(config["Bells"])
leds = LightController(config["Leds"])
