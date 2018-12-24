# define F_CPU 3300000UL

#include <inttypes.h>
#include <avr/io.h>
#include <util/delay.h>
#include <avr/interrupt.h>

#define BAUD_Rate 9600
#define BAUD_Register_Value ((32UL * F_CPU)/(16UL * BAUD_Rate))

#define true 1
#define false 0

#define ADDRESS 12


#define PIN_CLAPPER 0x20
#define PIN_DAMPER 0x8


struct _rx
{
	uint8_t mode;
	uint8_t address;
} rx;


void ioinit (void) {
	// scale back periferal clock
	CPU_CCP = 0xD8;
	CLKCTRL.MCLKCTRLB = CLKCTRL_PDIV_12X_gc | CLKCTRL_PEN_bm;

	// set io ouputs
	PORTA.DIR = PIN_DAMPER | PIN_CLAPPER;

	// setup uart
	USART0.BAUD = BAUD_Register_Value;
	USART0.CTRLA |= USART_RXCIE_bm;
	USART0.CTRLB |= USART_RXEN_bm;
	
	// setup timers
	TCA0.SINGLE.INTCTRL |= TCA_SINGLE_OVF_bm;
	TCA0.SINGLE.CTRLA |= (0x7 << 1);

	TCB0.CTRLA = TCB_CLKSEL_CLKDIV2_gc;
	TCB0.CTRLB = TCB_CNTMODE_SINGLE_gc | TCB_CCMPEN_bm;
	// TCB0.INTCTRL = 1;

	// enable global interupts
	CPU_SREG |= CPU_I_bm;
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
	/* === USART rx interrupt ===
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
	uint8_t value = USART0.RXDATAL;

	// get instruction type
	if (value & 0x80) {
		rx.address = value & 0x3F;
		rx.mode = (value >> 6) & 0x1;
	} else if (rx.address == ADDRESS) {
		// only bother parsing commands addressed to us
		if (rx.mode) {
			// TODO: configs
		} else {
			if ((value >> 5) & 0x3) {
				// dampen bell
				PORTA.OUT |= PIN_DAMPER;
				// start timer
				TCA0.SINGLE.CTRLECLR |= 0x2 << 2; 
				TCA0.SINGLE.PER = 0x2ff;
				TCA0.SINGLE.CTRLA |= TCA_SINGLE_ENABLE_bm;
			} else {
				// turn off damper (if it's still on)
				PORTA.OUT &= ~PIN_DAMPER;
				// ring bell using Timer B
				TCB0.CCMP = (value & 0x1F) << 11;
				TCB0.CNT = 0;
				TCB0.CTRLA |= TCB_ENABLE_bm;
			}
		}
	}
}


int main (void) {
	rx.address = 0;
	ioinit();
	while(1) {
		// global loop of nothing
		// everything is handled by interrupts
		_delay_ms(10);
	}
	return (0);
}
