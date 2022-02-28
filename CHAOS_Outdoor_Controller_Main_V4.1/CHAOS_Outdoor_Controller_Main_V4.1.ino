/*
*   This code pushes data up to the serial port on a regular timebase using the "SEND" method
*   It also sets internal variables using the "SET" method
*   The loop consists of three tasks:
*     1. Collecting data from each sensor
*     2. Passing the data up the serial port
*     3. Checking the serial buffer for any inbound messages
*     4. Parsing the data and setting any variables based on incoming data
*     
*     In a full application, a "compute" task is added for automated function
*/
#include "Treau_Controller.h"

unsigned char Ser_Temp;
unsigned char Ser2_Temp;
unsigned int Ser_Val_Temp;
unsigned int Fan_Speed = 205;
unsigned int Valve_Pos = 250;
unsigned int Pump_Speed = 0;
unsigned int Print_Status = 1;

unsigned int Raw_AD_Val[20];    // array to hold AD readings

void setup() {
  // put your setup code here, to run once:
  analogReference(EXTERNAL);
  // initialize the LED pin as an output:
  pinMode(ledPin, OUTPUT);
  pinMode(Compressor_On, OUTPUT);
  pinMode(Rev_Valve, OUTPUT);
  pinMode(DRV_STEP, OUTPUT);
  pinMode(DRV_DIR, OUTPUT);
  pinMode(DRV_NENBL, OUTPUT);
  pinMode(Fan_PWM, OUTPUT);  // sets the pin as output

  // Initialize hardware I/O states
  digitalWrite(DRV_NENBL, HIGH);   // Turn off stepper
  
  // Blink the LED as an "alive" indicator
  digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
  delay(200);                       // wait for a second
  digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
  delay(200);                       // wait for a second
 
  Serial.begin(115200);   // START COMMUNICATION TO HOST COMPUTER
  Serial2.begin(115200);  // START COMMUNICATION TO INDOOR UNIT OR AUXILIARY SERIAL INTERFACE

  Serial.println("CHAOS Outdoor Controller Ver4.00");
  Serial.println("Program beginning now.");

  // Put all component initializations here 
  // analogWrite(Fan_PWM, Fan_Speed); // analogRead values go from 0 to 1023, analogWrite values from 0 to 
  // Serial.println("Starting Condenser Fan Now.");
  Initialize_ExpValve(HOME_CLOSED);  // Send the Expansion Valve to fully-closed position
}

void loop() {
  // put your main code here, to run repeatedly:
  // ***************************************************
  // Read each sensor and push values up the serial port:
  // For this rev of software, since there are so few values to read, just grab them all here & print each one
  // ***************************************************
  if (Print_Status == 1) {
    Serial.print("DATA,");
    for(int i = 0; i < 8; i++){
      Raw_AD_Val[i] = analogRead(i);      
      Serial.print(Raw_AD_Val[i]);
      Serial.print(",");
    }
    Serial.print(Valve_Pos);
    Serial.print(",");
    Serial.println("EOD");
    delay(10000);
    }
    
  if (Serial2.available() > 0) {
    Ser2_Temp = Serial2.read();
    Serial.write(Ser2_Temp);    // just echo back for now
  }
  
  if (Serial.available() > 0) {
      // get incoming byte:
      Ser_Temp = Serial.read();
      // Serial.println(Ser_Temp);
      digitalWrite(LED_BUILTIN, HIGH);  // turn the LED on (HIGH is the voltage level)
      delay(20);                        // wait for a second
      digitalWrite(LED_BUILTIN, LOW);   // turn the LED off by making the voltage LOW
      delay(20);                        // wait for a second    
      switch (Ser_Temp) 
      {
        case 'a':
        {
          Print_Status = Serial.parseInt();
          }
        break;
        case 'v':
        {
          Ser_Val_Temp = Serial.parseInt();
          Serial.print("Serial Port Value is: ");
          Serial.println(Ser_Val_Temp);
          Set_Valve(Ser_Val_Temp);
          Serial.print("New Valve Position is: ");
          Serial.println(Valve_Pos);        
          }
        break;
        
        case 'c':
        {
            Serial.print("Current Valve Position is: ");
            Serial.println(Valve_Pos);                
        }
        break;
  
        case 'r':
        {
          Ser_Val_Temp = Serial.parseInt();
          Serial.print("Serial Port Value is: ");
          Serial.println(Ser_Val_Temp);
          Fan_Speed = 255 - Ser_Val_Temp;
          analogWrite(Fan_PWM, Fan_Speed); // analogRead values go from 0 to 1023, analogWrite values from 0 to 
          Serial.print("Fan Speed is: ");
          Serial.println(255 - Fan_Speed);        
        }
        break;
  
        case 'p':
        {
          Ser_Val_Temp = Serial.parseInt();
          Serial.print("Serial Port Value is: ");
          Serial.println(Ser_Val_Temp);
          Pump_Speed = Ser_Val_Temp;
          // SetVal_dPot(Pump_Speed, p_PUMP);    // Pass pump speed value into the digital potentiometer
          Serial.print("New Pump Speed is: ");
          Serial.println(Pump_Speed);        
        }
        break;
    
        case 'f':
        case 'F':
        {
          Fan_Speed = Fan_Speed - 10;
          if(Fan_Speed < 20)
          {
            Fan_Speed = 0;
          }
          analogWrite(Fan_PWM, Fan_Speed); // analogRead values go from 0 to 1023, analogWrite values from 0 to 
          Serial.println("Fan SPEED UP");
  
        }
        break;
        
        case 's':
        case 'S':
        {
         Fan_Speed = Fan_Speed + 10;
          if(Fan_Speed > 240)
          {
            Fan_Speed = 240;
          }
          analogWrite(Fan_PWM, Fan_Speed); // analogRead values go from 0 to 1023, analogWrite values from 0 to 
          Serial.println("Fan SLOW DOWN");
  
        }
        break;
  
        case 'h':
        {
           digitalWrite(Rev_Valve, HIGH);    // turn the LED off by making the voltage LOW
           Serial.println("Heating Mode ON");
        }
        break;
  
        case 'g':
        {
           digitalWrite(Rev_Valve, LOW);    // turn the LED off by making the voltage LOW
           Serial.println("Heating Mode OFF");
        }
        break;
  
        default:
        // statements
        break;
      }
    }
    delay(100);
            
  /* AD TEST
  Serial.print("DATA,");
  Raw_AD_Val[0] = analogRead(0);      
  Serial.print(Raw_AD_Val[0]);
  Serial.print(",");
  
  Raw_AD_Val[1] = analogRead(1);      
  Serial.print(Raw_AD_Val[1]);
  Serial.print(",");
  
  Raw_AD_Val[2] = analogRead(2);      
  Serial.print(Raw_AD_Val[2]);
  Serial.print(",");
  
  Raw_AD_Val[3] = analogRead(3);      
  Serial.print(Raw_AD_Val[0]);
  Serial.print(",");
  
  Raw_AD_Val[4] = analogRead(4);      
  Serial.print(Raw_AD_Val[5]);
  Serial.print(",");
  
  Raw_AD_Val[5] = analogRead(5);      
  Serial.print(Raw_AD_Val[5]);
  Serial.print(",");
  
  Raw_AD_Val[6] = analogRead(6);      
  Serial.print(Raw_AD_Val[6]);
  Serial.print(",");
  
  Raw_AD_Val[7] = analogRead(7);      
  Serial.print(Raw_AD_Val[7]);
  Serial.print(",");
  
  Serial.println("EOD");
  // END AD TEST
  */
}

void Initialize_ExpValve(int Home_Direction){
  // This function drives the expansion valve to a home in whichever direction is specified
  if(Home_Direction == HOME_OPEN){
    digitalWrite(DRV_DIR, LOW);     // Set the direction of the stepper motor control. LOW = OPEN
    Serial.println("Initializing Expansion Valve to Fully Open");         
    }
  else{
    digitalWrite(DRV_DIR, HIGH);     // Set the direction of the stepper motor control. HIGH = CLOSED
    Serial.println("Initializing Expansion Valve to Fully Closed");         
    }

  digitalWrite(DRV_NENBL, LOW);   // Turn on stepper
  delay(10);
  for (int i = 0; i <= 255; i++){
    digitalWrite(DRV_STEP, HIGH);
    delay(15);
    digitalWrite(DRV_STEP, LOW);
    delay(15);
    }
    
  digitalWrite(DRV_NENBL, HIGH);   // Turn off stepper

  // Make sure we initialize the valve position state variable based on the HOME_OPEN vs. HOME_CLOSED state
  if(Home_Direction == HOME_OPEN){
    Valve_Pos = 250;
    }
  else {
    Valve_Pos = 0;
    }
  Serial.println("Initializing Expansion Valve Complete");         
}

unsigned int Set_Valve(unsigned int New_Valve_Pos)
{
  if(New_Valve_Pos > Valve_Pos){
    digitalWrite(DRV_DIR, LOW);     // Set the direction of the stepper motor control. LOW = OPEN
    digitalWrite(DRV_NENBL, LOW);   // Turn on stepper

    while(New_Valve_Pos > Valve_Pos)
    {
      // Send a pulse to the stepper motor, and increment position value
      Valve_Pos++;
      digitalWrite(DRV_STEP, HIGH);
      delay(15);
      digitalWrite(DRV_STEP, LOW);
      delay(15);     
    }

    digitalWrite(DRV_NENBL, HIGH);   // Turn off stepper
  }

  else if(New_Valve_Pos < Valve_Pos)
  {
    digitalWrite(DRV_DIR, HIGH);     // Set the direction of the stepper motor control. HIGH = CLOSED
    digitalWrite(DRV_NENBL, LOW);   // Turn on stepper

    while(New_Valve_Pos < Valve_Pos)
    {
      // Send a pulse to the stepper motor, and decrement position value
      Valve_Pos--;
      digitalWrite(DRV_STEP, HIGH);
      delay(15);
      digitalWrite(DRV_STEP, LOW);
      delay(15);     
    }

    digitalWrite(DRV_NENBL, HIGH);   // Turn off stepper
  }
    return Valve_Pos;

}

/*
  digitalWrite(DRV_DIR, LOW);

  for (int i = 0; i <= 255; i++)
  {
    digitalWrite(DRV_STEP, HIGH);
    delay(15);
    digitalWrite(DRV_STEP, LOW);
    delay(15);
    
  }


  digitalWrite(DRV_DIR, HIGH);


  for (int i = 0; i <= 255; i++)
  {
    digitalWrite(DRV_STEP, HIGH);
    delay(15);
    digitalWrite(DRV_STEP, LOW);
    delay(15);
    
  }

*/  
