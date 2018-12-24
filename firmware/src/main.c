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
	uint8_t mode;
	uint8_t address;
} rx;


void ioinit (void) {
	// set io ouputs
	PORTA.DIR = PIN_TXD | PIN_DAMPER | PIN_CLAPPER;

	// setup uart
	USART0.BAUD = BAUD_Register_Value;
	USART0.CTRLA |= USART_RXCIE_bm;
	USART0.CTRLB |= USART_RXEN_bm;
	
	// setup timers
	TCA0.SINGLE.INTCTRL |= TCA_SINGLE_OVF_bm;
	TCA0.SINGLE.CTRLA |= (0x7 << 1);

	TCB0.CTRLA = TCB_CLKSEL_CLKTCA_gc;
	TCB0.CTRLB = TCB_CNTMODE_SINGLE_gc;
	TCB0.INTCTRL = 1;

	// enable global interupts
	CPU_SREG |= CPU_I_bm;
}



// Timer A finishes
ISR(TCA0_OVF_vect) {	
	// Clear the interrupt
	TCA0.SINGLE.INTFLAGS = 0xff;
	// halt and restart the timer
	TCA0.SINGLE.CTRLA &= ~TCA_SINGLE_ENABLE_bm;
	TCA0.SINGLE.CTRLECLR |= 0x2 << 2; 
	// turn off the coil
	PORTA.OUT &= ~PIN_CLAPPER;
}


ISR(TCB0_INT_vect) {
	PORTA.OUT ^= PIN_DAMPER;
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
		rx.mode = (value >> 6) & 0x1;
	} else if (rx.address == ADDRESS) {
		// only bother parsing commands to us
		if (rx.mode) {
			// TODO: configs
		} else {
			if (((value >> 5) & 0x3) == 0) {
				// Dampen Bell
				TCB0.CTRLA |= TCB_ENABLE_bm;
				TCB0.CCMP = 0xff;
			} else {
				// Ring Bell
				PORTA.OUT |= PIN_CLAPPER;
				// start timer
				TCA0.SINGLE.PER = (value & 0x1F) << 3;
				TCA0.SINGLE.CTRLA |= TCA_SINGLE_ENABLE_bm;
			}
		}
	}
	// USART0.TXDATAL = rx;
}



int main (void) {
	ioinit();
	rx.address = 0;
	while(1) {
		_delay_ms(20);
	}
	return (0);
}
