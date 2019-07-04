import os

while True:
    print("----------------------")
    address = str(input("Enter Address: "))

    # exit loop
    if address.lower().strip() in ["exit", "quit", "q", "stop"]:
        break
    else:
        address = int(address)

    # write address to the config file
    config_file = open("my_address.h", "w")
    config_file.write("#define MY_ADDRESS %d\n" % address)
    config_file.close()

    # compile with new address
    os.system("make")

    print("Flashing...")

    # flash to chip
    os.system("./flash.sh")
