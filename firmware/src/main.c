# define F_CPU 3300000UL

#include <inttypes.h>
#include <avr/io.h>
#include <util/delay.h>
#include <avr/interrupt.h>

#define BAUD_Rate (9600)
#define BAUD_Register_Value ((64UL * F_CPU)/(16UL * BAUD_Rate))

#define true 1
#define false 0

#define ADDRESS 12


#define PIN_CLAPPER 0x8
#define PIN_DAMPER  0x2
#define PIN_TXD     0x20


struct _rx
{
	uint8_t flag;
	uint8_t cmd;
	uint8_t cmd_mode;
	uint8_t value;
	uint8_t address;
} rx;


void ioinit (void) {
	// set io ouputs
	PORTA.DIR = PIN_TXD | PIN_DAMPER | PIN_CLAPPER;

	// setup uart
	USART0.BAUD = BAUD_Register_Value;
	USART0.CTRLA |= USART_RXCIE_bm;
	USART0.CTRLB |= USART_TXEN_bm | USART_RXEN_bm;
	
	// enable global interupts
	CPU_SREG |= CPU_I_bm;
}


// USART rx interrupt
/*

1-m-aaaaaa : mode(1),  address(6)

Mode #0:
	0-cc-vvvvv : cmd(2), value(5)

		cmd 0 = Ring
		cmd 1 = Damp
		cmd 2 = Mortello
		cmd 3 = Buzz 

Mode #1:
	0-pp-vvvvvv : param(2), value(6)

		param 0 = min ring value
		param 1 = max ring value
		param 2 = buzz value
		param 3 = latency?

*/
ISR(USART0_RXC_vect) {
	uint8_t value = USART0.RXDATAL;

	// get instruction type
	if (value & 0x80) {
		rx.address = value & 0x3F;
		rx.cmd_mode = (value >> 6) & 0x1;
	} else if (rx.address == ADDRESS) {
		// only bother parsing commands to us
		if (rx.cmd_mode) {
			// TODO: configs
		} else {
			rx.flag = true;
			rx.value = value & 0x1F;
			rx.cmd = (value >> 5) & 0x3;
		}
	}
	// USART0.TXDATAL = rx;
}



int main (void) {
	ioinit();

	rx.flag = false;
	rx.address = 0;




	while(1) {


		if (rx.flag) {
			rx.flag = false;

			if (rx.cmd == 0) {
				// ring
				PORTA.OUT |= PIN_CLAPPER;
				for (int t = 0; t < rx.value; t++) {
					_delay_ms(1);
				}
			} else if (rx.cmd == 1) {
				// dampen
				PORTA.OUT |= PIN_DAMPER;
				_delay_ms(100);

			}

			PORTA.OUT &= 0xf0;
		}
		_delay_ms(10);
	}
	return (0);
}
