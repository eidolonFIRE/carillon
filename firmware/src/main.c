# define F_CPU 5000000UL

#include <inttypes.h>
#include <avr/io.h>
#include <avr/sleep.h>
#include <util/delay.h>


void ioinit (void)
{
    // set porta_2 to output
    PORTA.DIR = 0xf;
}


int main (void)
{

    ioinit ();


    while(1) {
        

        PORTA.OUT = 0x0f;

        _delay_ms(20);

        PORTA.OUT = 0x0;

        _delay_ms(500);


    }

    return (0);
}
