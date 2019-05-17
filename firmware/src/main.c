# define F_CPU 3300000UL

#include <inttypes.h>
#include <avr/io.h>
#include <util/delay.h>
#include <avr/interrupt.h>

#define BAUD_RATE 38400
#define PIN_CLAPPER 0x20
#define PIN_DAMPER 0x8

#define IS_SETUP_SIGNATURE 0xAAAA

struct _rx {
	uint8_t mode;
	uint8_t address;
	uint8_t param;
} rx;

struct _config {
	uint8_t my_address;
	uint16_t clapper_min;
	uint16_t clapper_max;
} config;

enum _eeprom_address {
	E2_ADDR_MY_ADDRESS = 0,
	E2_ADDR_CLAPPER_MIN = 1,
	E2_ADDR_CLAPPER_MAX = 2,
	E2_ADDR_IS_SETUP_SIG = 3,
};


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


void write_user_row_byte(uint8_t address, uint8_t value) {
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

	// write to user EEPROM page
	(*((volatile uint8_t *)(&USERROW + address * 2))) = value;

	// disarm write-protection and execute write command
	CPU_CCP = CCP_SPM_gc;
	NVMCTRL.CTRLA = NVMCTRL_CMD_PAGEWRITE_gc;
}


uint8_t read_user_row_byte(uint8_t address) {
	return *(uint8_t *)(&USERROW + address * 2);
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


ISR(USART0_RXC_vect) {
	/*=====( RX protocol )=====
		1-m-aaaaaa : mode(1),  address(6)

		Mode 0:
			0-c-vvvvvv : cmd(1), value(6)
				cmd 0 = Ring
				cmd 1 = Damp

		Mode 1:  -- MULTI BYTE --
			[0] 0-ppppppp : parameter(7)
				  0x00 = --reserved--
				  0x01 = min clap value
				  0x02 = max clap value
				  0x03 = set address
				  0xFF = commit EEPROM data

			[1] 0-vvvvvvv : value(7)

	*/
	uint8_t msg = USART0.RXDATAL;

	// get instruction type
	if (msg & 0x80) {
		rx.address = msg & 0x3F;
		rx.mode = (msg >> 6) & 0x1;
		rx.param = 0;
	} else if (rx.address == config.my_address) {
		if (rx.mode) {
			if (rx.param) {
				if (rx.param == 0x01) {
					// set clapper min power
					config.clapper_min = (msg & 0x7F) << 4;
				} else if (rx.param == 0x02) {
					// set clapper max power
					config.clapper_max = ((msg & 0x7F) << 1) + 0x18;
				} else if (rx.param == 0x03) {
					// set my_address
					if (read_eeprom_word(E2_ADDR_IS_SETUP_SIG) != IS_SETUP_SIGNATURE) {
						// not setup yet, read address and save
						config.my_address = msg & 0x3F;
						write_user_row_byte(E2_ADDR_MY_ADDRESS, config.my_address);
						// set signature flag so this can't happen again
						write_eeprom_word(E2_ADDR_IS_SETUP_SIG, IS_SETUP_SIGNATURE);
					}
				} else if (rx.param == 0xFF) {
					// write config to EEPROM
					write_eeprom_word(E2_ADDR_CLAPPER_MIN, config.clapper_min);
					write_eeprom_word(E2_ADDR_CLAPPER_MAX, config.clapper_max);
				}	
			} else {
				rx.param = msg & 0x7F;
			}

		} else {
			if (msg & 0x40) {
				// dampen bell
				PORTA.OUT |= PIN_DAMPER;
				// start timer
				TCA0.SINGLE.CTRLECLR |= 0x2 << 2; 
				TCA0.SINGLE.PER = (msg & 0x3F) << 4; // 0x2ff;
				TCA0.SINGLE.CTRLA |= TCA_SINGLE_ENABLE_bm;
			} else {
				// force damper off
				PORTA.OUT &= ~PIN_DAMPER;
				// clap bell using Timer B
				TCB0.CCMP = config.clapper_min + ((msg & 0x3F) * config.clapper_max);
				TCB0.CNT = 0;
				TCB0.CTRLA |= TCB_ENABLE_bm;
			}
		}
	}
}


int main (void) {
	// load settings from eeprom
	if (read_eeprom_word(E2_ADDR_IS_SETUP_SIG) == IS_SETUP_SIGNATURE) {
		config.my_address = read_user_row_byte(E2_ADDR_MY_ADDRESS);
	} else {
		config.my_address = 0;
	}
	config.clapper_min = read_eeprom_word(E2_ADDR_CLAPPER_MIN);
	config.clapper_max = read_eeprom_word(E2_ADDR_CLAPPER_MAX);

	// initial state
	rx.address = 0;
	rx.mode = 0;
	rx.param = 0;

	ioinit();
	while(1) {
		// global loop of nothing, everything is handled by interrupts
		_delay_ms(10);
	}
	return (0);
}
