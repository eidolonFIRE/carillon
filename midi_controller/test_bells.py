from bells import BellsController
# from leds import LightController
import sys
import mido
import threading
import json
from time import sleep, time
import random

# LOAD CONFIG
config = json.load(open('config.json', 'r'))

# Spin up main objects
bells = BellsController(config["Bells"])



def major_chord(note, vel):
    bells.ring(note, vel)
    bells.ring(note + 4, vel)
    bells.ring(note + 7, vel)


def arp_seq(arpegio, vel, delay):
    for note in arpegio:
        bells.ring(note, vel)
        sleep(delay)


ARP_44_Major_I_IV_I_V = [55, 55, 60, 60, 64, 64, 67, 67, 55, 55, 60, 60, 64, 64, 67, 67, 57, 57, 60, 60, 65, 65, 69, 69, 57, 57, 60, 60, 65, 65, 69, 69, 55, 55, 60, 60, 64, 64, 67, 67, 55, 55, 60, 60, 64, 64, 67, 67, 59, 59, 62, 62, 67, 67, 71, 71, 59, 59, 62, 62, 67, 67, 71, 71]
ARP_44_i_III_iv_V = [67, 67, 60, 60, 51, 51, 43, 43, 55, 55, 48, 48, 39, 39, 31, 31, 67, 67, 58, 58, 51, 51, 43, 43, 55, 55, 46, 46, 39, 39, 31, 31, 68, 68, 60, 60, 53, 53, 44, 44, 56, 56, 48, 48, 41, 41, 32, 32, 67, 67, 59, 59, 50, 50, 43, 43, 55, 55, 47, 47, 38, 38, 31, 31]
ARP_323_Major_44_I_iii_IV_V = [64, 64, 60, 60, 55, 55, 64, 64, 60, 60, 64, 64, 60, 60, 55, 55, 64, 64, 59, 59, 55, 55, 64, 64, 59, 59, 64, 64, 59, 59, 55, 55, 65, 65, 60, 60, 57, 57, 65, 65, 60, 60, 65, 65, 60, 60, 57, 57, 62, 62, 59, 59, 55, 55, 62, 62, 59, 59, 62, 62, 59, 59, 55, 55]


# Loop arpegios

for each in range(2):
    arp_seq(ARP_44_Major_I_IV_I_V, 20, 0.1)

for each in range(2):
    arp_seq(ARP_44_i_III_iv_V, 20, 0.1)


# SIMPLE SWEEP

# for note in range(48, 48 + bells.num_bells, 1):
#     print(note)
#     bells.ring(note, 20)
#     sleep(0.1)



# CHORD SWEEP

# for note in range(48, 40 + bells.num_bells, 2):
#     print(note)
#     major_chord(note, 20)
#     sleep(0.1)


# RANDOM

# for x in range(100):
#     note = random.randint(48, 48+bells.num_bells)
#     bells.ring(note, 20)
#     sleep(0.1)



    # for y in range(3):
    #     bells.ring(note + y * 2, 20)
    #     sleep(0.1)



# DAMP SWEEP

# for note in range(48, 48 + bells.num_bells, 1):
#     bells.ring(note, 20)
#     sleep(0.2)
#     bells.damp(note)


bells.close()

