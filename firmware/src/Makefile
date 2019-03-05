# Config

TOOLCHAIN = ../toolchain/avr8-gnu-toolchain-linux_x86_64
MCUPACK = ../toolchain/packs

MCU_TARGET     = attiny402

OPTIMIZE       = -O1

CC             = $(TOOLCHAIN)/bin/avr-gcc
CHEX           = $(TOOLCHAIN)/bin/avr-objcopy



all: main.elf

main.elf: main.o
	# make elf file from .o files
	$(CC) -o $@ $^   -Wl,-Map="main.map" -Wl,--start-group -Wl,-lm  -Wl,--end-group -Wl,--gc-sections -mmcu=$(MCU_TARGET) -B $(MCUPACK)/gcc/dev/$(MCU_TARGET)

	# make the hex file from elf file
	$(CHEX) -O ihex -R .eeprom -R .fuse -R .lock -R .signature -R .user_signatures  $@ $(@:%.elf=%.hex)

	# clean up other files
	rm -f *.d

main.o: main.c
	# compile code to .o
	$(CC) -x c -funsigned-char -funsigned-bitfields -DNDEBUG  -I$(MCUPACK)/include  $(OPTIMIZE) -ffunction-sections -fdata-sections -fpack-struct -fshort-enums -Wall -mmcu=$(MCU_TARGET) -B $(MCUPACK)/gcc/dev/$(MCU_TARGET) -c -std=gnu99 -MD -MP -MF "$(@:%.o=%.d)" -MT"$(@:%.o=%.d)" -MT"$@" -o $@ $<

clean:
	rm -rf *.o main.elf *.eps *.png *.pdf *.bak *.map
