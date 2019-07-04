import os
import subprocess
import json
import numpy as np


class cl:
    reset = '\033[0m'
    bold = '\033[01m'
    disable = '\033[02m'
    underline = '\033[04m'
    reverse = '\033[07m'
    strikethrough = '\033[09m'
    invisible = '\033[08m'

    class f:
        black = '\033[30m'
        red = '\033[31m'
        green = '\033[32m'
        orange = '\033[33m'
        blue = '\033[34m'
        purple = '\033[35m'
        cyan = '\033[36m'
        lightgrey = '\033[37m'
        darkgrey = '\033[90m'
        lightred = '\033[91m'
        lightgreen = '\033[92m'
        yellow = '\033[93m'
        lightblue = '\033[94m'
        pink = '\033[95m'
        lightcyan = '\033[96m'

    class b:
        black = '\033[40m'
        red = '\033[41m'
        green = '\033[42m'
        orange = '\033[43m'
        blue = '\033[44m'
        purple = '\033[45m'
        cyan = '\033[46m'
        lightgrey = '\033[47m'


# LOAD bell layout
config = json.load(open('../../midi_controller/config.json', 'r'))
bells = np.array(config["Leds"]["note_array"])
addresses = bells.reshape(1, 27)[0]

is_done = set()


def print_grid(sel):
    l1 = "  __  "
    l2 = " /{:2}\\ "
    l3 = " \\__/ "

    for y in range(3):

        bumper_space = " " * (2 * (2 - y))
        row = bells[:, 2 - y]

        print(bumper_space + l1 * 9)
        print(bumper_space + "".join([((cl.f.lightgreen if row[x] in is_done else cl.reset) + (cl.bold if row[x] == sel else "") + l2.format(row[x])) for x in range(9)]))
        print(bumper_space + l3 * 9)



for addr in addresses:
    print(cl.reset)
    print_grid(addr)

    # write address to the config file
    config_file = open("my_address.h", "w")
    config_file.write("#define MY_ADDRESS %d\n" % addr)
    config_file.close()

    # compile with new address
    output = subprocess.run(['make'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    if "error" in output:
        print(cl.bold + cl.f.lightred + "Error Compiling for addr: {}".format(addr))
        break

    # flash to chip
    input("\nPress Enter to Flash {}".format(addr))
    output = subprocess.run(['python', '../toolchain/pyupdi/pyupdi.py', '-d', 'tiny402', '-c', '/dev/ttyUSB0', '-f', 'main.hex'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode('utf-8')
    while "success" not in output:
        input(cl.bold + cl.f.red + "Flashing Failed. Press Enter to Reflash {}".format(addr))
        output = subprocess.run(['python', '../toolchain/pyupdi/pyupdi.py', '-d', 'tiny402', '-c', '/dev/ttyUSB0', '-f', 'main.hex'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode('utf-8')

    print(cl.bold + cl.f.lightgreen + "Completed: {}".format(addr))
    is_done.add(addr)



