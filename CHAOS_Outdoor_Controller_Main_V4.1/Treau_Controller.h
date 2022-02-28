/*

Arduino Pins:
A0  = Pressure - Low Side
A1  = Pressure - High Side
A2  = Temperature - Low Side
A3  = Temperature - High Side
A4  = Water_In Temperature
A5  = Water_Out Temperature

D2  = Fan_PWM
D18 = Dan_Diag_Logic (are these interrupt inputs? they are also SERIAL_1)
D19 = DRV_NFault (are these interrupt inputs? they are also SERIAL_1)
D22 = Max5389_CSA (0-10k resistance for compressor)
D23 = Max5389_CSB (0-5V for pump)
D24 = Max5389_UDA (0-10k resistance for compressor)
D25 = Max5389_UDB (0-5V for pump)
D26 = Max5389_INCA (0-10k resistance for compressor)
D27 = Max5389_INCB (0-5V for pump)
D30 = Compressor_On
D31 = Reversing Valve
D40 = DRV_Reset
D41 = DRV_SM1
D42 = DRV_SM0
D43 = DRV_DIR
D44 = DRV_STEP
D45 = DRV_NHOME
D46 = DRV_NENBL

*/


const int ledPin =  13;  
const int Compressor_On = 30;
const int Rev_Valve = 31;

const int DRV_STEP = 44;
const int DRV_DIR = 43;
const int DRV_NENBL = 46;
const int Fan_PWM = 2;

#define HOME_OPEN 0
#define HOME_CLOSED 1


/**********************************
 * DRV8805 Stepper Motor Control
 * http://www.ti.com/lit/ds/symlink/drv8805.pdf
 * DRV_NENBL must be low or tri-state for outputs to be enabled
 * DRV_Reset clears the internal logic of the 8805 when pulled high. It should be low or tri-state output
 * DRV_SM0 and DRV_SM1 control step modes
 * 
 * SM1  SM0 MODE
 *   0  0   2-phase drive (full step)
 *   0  1   1-2 phase drive (half step)
 *   1  0   1-phase excitation (wave drive)
 *   1  1   Reserved
 *
 * 
 */
