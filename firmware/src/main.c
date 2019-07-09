# define F_CPU 3300000UL

#include <inttypes.h>
#include <avr/io.h>
#include <util/delay.h>
#include <avr/interrupt.h>
#include "my_address.h"

#define BAUD_RATE 38400
#define PIN_CLAPPER 0x20
#define PIN_DAMPER 0x8
#define E2_COMMIT_KEY 0x1D

enum e2_table {
	E2_ADDR_CLAPPER_MIN,
	E2_ADDR_CLAPPER_MAX,
};

enum rx_commands {
	CMD_RESERVED = 0x0,
	CMD_RING = 0x1,
	CMD_RING_M = 0x2,
	CMD_DAMP = 0x3,
	CMD_SET_CLAPPER_MIN = 0x10,
	CMD_SET_CLAPPER_MAX = 0x20,
	CMD_COMMIT_E2 = 0x30,
};

struct _rx {
	uint8_t addr;
	uint8_t cmd;
} rx;

struct _config {
	uint16_t clapper_min;
	uint16_t clapper_max;
} config;


void ioinit (void) {
	// disarm write-protection
	CPU_CCP = CCP_IOREG_gc;
	// scale back periferal clock
	CLKCTRL.MCLKCTRLB = CLKCTRL_PDIV_12X_gc | CLKCTRL_PEN_bm;
	// CLKCTRL.MCLKCTRLB = CLKCTRL_PDIV_2X_gc | CLKCTRL_PEN_bm;

	// set io ouputs
	PORTA.DIR = PIN_DAMPER | PIN_CLAPPER;

	// setup uart
	USART0.BAUD = ((32UL * F_CPU)/(16UL * BAUD_RATE));
	USART0.CTRLA |= USART_RXCIE_bm;
	USART0.CTRLB |= USART_RXEN_bm;
	
	// setup timers
	TCA0.SINGLE.INTCTRL |= TCA_SINGLE_OVF_bm;
	TCA0.SINGLE.CTRLA |= (0x7 << 1);
	TCB0.CTRLA = TCB_CLKSEL_CLKDIV2_gc;
	TCB0.CTRLB = TCB_CNTMODE_SINGLE_gc | TCB_CCMPEN_bm;

	// enable global interupts
	CPU_SREG |= CPU_I_bm;
}


void write_eeprom_word(uint8_t address, uint16_t value) {
	// wait for status ready
	uint8_t timeout = 0;
	while (NVMCTRL.STATUS & NVMCTRL_EEBUSY_bm) {
		// BUSY!
		_delay_ms(1);
		timeout++;
		if (timeout >= 100) {
			// abort...
			return;
		}
	}

	// setup write command
	(*((volatile uint16_t *)(EEPROM_START + address * 2))) = value;

	// disarm write-protection and write
	CPU_CCP = CCP_SPM_gc;
	NVMCTRL.CTRLA = NVMCTRL_CMD_PAGEWRITE_gc;
}

uint16_t read_eeprom_word(uint8_t address) {
	return *(uint16_t *)(EEPROM_START + address * 2);
}


// Timer A finishes
ISR(TCA0_OVF_vect) {	
	// Clear the interrupt
	TCA0.SINGLE.INTFLAGS = 0xff;
	// halt the timer
	TCA0.SINGLE.CTRLA &= ~TCA_SINGLE_ENABLE_bm;
	// turn off the coil
	PORTA.OUT &= ~PIN_DAMPER;
}


void ring_bell(uint8_t velocity, uint8_t mortello) {
	if (!mortello) {
		// force damper off
		PORTA.OUT &= ~PIN_DAMPER;
	}
	// clap bell using Timer B
	TCB0.CCMP = config.clapper_min + (velocity * config.clapper_max / 2);
	TCB0.CNT = 0;
	TCB0.CTRLA |= TCB_ENABLE_bm;
}


void dampen_bell(uint8_t duration) {
	// dampen bell
	PORTA.OUT |= PIN_DAMPER;
	// start timer
	TCA0.SINGLE.CTRLECLR |= TCA_SINGLE_CMD1_bm; 
	TCA0.SINGLE.PER = duration << 4;
	TCA0.SINGLE.CTRLA |= TCA_SINGLE_ENABLE_bm;
}


void process_rx(uint8_t cmd, uint8_t value) {
	switch (cmd) {
		case CMD_RING:
			ring_bell(value, 0);
			break;
		case CMD_RING_M:
			ring_bell(value, 1);
			break;
		case CMD_DAMP:
			dampen_bell(value);
			break;
		case CMD_SET_CLAPPER_MIN:
			config.clapper_min = value << 4;
			break;
		case CMD_SET_CLAPPER_MAX:
			config.clapper_max = value + 0x10;
			break;
		case CMD_COMMIT_E2:
			if (value == E2_COMMIT_KEY) {
				write_eeprom_word(E2_ADDR_CLAPPER_MIN, config.clapper_min);
				write_eeprom_word(E2_ADDR_CLAPPER_MAX, config.clapper_max);
			}
			break;
		default:
			// Invalid command!
			return;
	}
}


ISR(USART0_RXC_vect) {
	/*===============( 3-byte RX protocol )===============
		[0] 1-aaaaaaa : addr(7)
		[1] 0-ppppppp : cmd(7)  ...see enum
		[2] 0-vvvvvvv : value(7)
	=====================================================*/
	uint8_t msg = USART0.RXDATAL;
	if (msg & 0x80) {
		rx.addr = msg & 0x3F;
		rx.cmd = 0;
	} else {
		if (rx.cmd) {
			if (rx.addr == MY_ADDRESS) {
				process_rx(rx.cmd, msg & 0x7F);
			}
			rx.addr = 0xFF;
			rx.cmd = 0x0;
		} else {
			rx.cmd = msg & 0x7F;
		}
	}
}


int main(void) {
	// load config
	config.clapper_min = read_eeprom_word(E2_ADDR_CLAPPER_MIN);
	config.clapper_max = read_eeprom_word(E2_ADDR_CLAPPER_MAX);

	// initial state
	rx.addr = 0xFF;
	rx.cmd = 0;

	ioinit();
	while(1) {
		// global loop of nothing, everything is handled by interrupts
		_delay_ms(10);
	}
	return (0);
}
