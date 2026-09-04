/*========================================================================*/
/*                Final Project  -  Find Water                            */
/*========================================================================*/
/* Main Goal: 
 *   intake commands from RP3 and execute them
 *   
 * Notes:   
 *   most logic is gonna be in the .py files
 *
 *
--------------------------------------------------------------------------*/

/* ------------------- Include ------------------- */ 
#include <Wire.h>                // include the PRIZM library in the sketch
#include <PRIZM.h>               // include the PRIZM library in the sketch


/* ------------------- Objects ------------------- */
PRIZM prizm;                     // instantiate a PRIZM object “prizm” so we can use its functions


/* ------------------- Tunables ------------------ */
// Port Information:
int SENSOR_PORT = 3;         // Sensor port (assumed)

// Acknoledgement:
String inputString = "";         // a string to hold incoming data
boolean stringComplete = false;  // whether the string is complete
String outputString = "";        // a string to hold outgoing data

// Commands:
int cmd = 0;                // INT - to store the cmd
String cmdStr = "";         // a string to store the cmd

// Movements:
int power = 11;     //TODO: MAY CHANGE BACK TO WHAT WE HAD FOR LAB 3 WHERE WE SENT POWER


/* ------------- Function Prototypes ------------- */
//void setup();
//void loop();  
void cmdRead(int cmd);
//void serialEvent();




/*============================================================*/
/*                       Set up function                      */
/*============================================================*/
/*      1. Get PRIZM set up
 *      2. initialize Serial event stuff
 *      3. Set up string reserves 
 * ------------------------------------------------------------*/
void setup() {
    prizm.PrizmBegin();            // start prizm
    prizm.setMotorInvert(1,1);     // invert the direction of DC Motor 1 to harmonize the direction of opposite facing drive motors
                                 
    Serial.begin(9600);            // initialize serial:
  
    // reserve 20/10 bytes for the string:
    inputString.reserve(20);
    outputString.reserve(20);
    cmdStr.reserve(10);
}



/*========================================================================*/
/*                         MAIN FUNCTION                                  */
/*========================================================================*/
/* Basic Idea (steps): 
 *           
 *      1 - Recieve and Setup with input string
 *           
 *      2 - Interpret command and execute it 
 *           
 *      3 - print output string as ack 
 *           
 *      4 - clear data for next event
 *    
--------------------------------------------------------------------------*/
void loop() {

    if (stringComplete) {

        // 1 - Intake Commands/Grab new serial data: 
        inputString.trim();                     // remove whitespace characters  (NOTE: may not need this)
        cmdStr = inputString.substring(0, 1);   // read first char only from input string
        cmd = cmdStr.toInt();                   // convert read char into integer


        // 2 - Interpret command and execute it
        cmdRead(cmd);


        // 3 - Print output string
        Serial.println(outputString);    // use println to add a '\n' at the end of our msg/ack       


        // 4 - Clear the variables to wait for another cmd sending
        inputString = "";
        outputString = "";
        cmdStr = "";
        cmd = 0;
        stringComplete = false;
    }
}






/*========================================================================*/ 
/*                             COMMAND READ                               */ 
/*========================================================================*/ 
/* Commands: 
 *           
 *        1  -  Handshake
 *           
 *        2  -  Turn Left 
 *           
 *        3  -  Turn Right  
 *           
 *        4  -  Read Sonic Sensor (CM)
 *           
 *        5  -  Break
 *           
 *        6  -  Go Forward
 *           
 *        7  -  Go Backward
 *
 *------------------------------------------------------------------------*/ 
void cmdRead(int cmd) {    
    switch (cmd) {

        case 1: {                   // 1 = Handshake
            outputString += "1";               
            break;
        }

        case 2: {                   // 2 = Read Sonic Sensor (CM)
            outputString = "";                
            outputString += prizm.readSonicSensorCM(SENSOR_PORT);
            break;
        }

        case 3: {                   // 3 = Go Forward
            outputString += "3";         
            prizm.setMotorPowers(power, power);
            break;
        }

        case 4: {                   // 4 = Go Backward
            outputString += "4";           
            prizm.setMotorPowers(-power, -power);
            break;
        }

        case 5: {                   // 5 = Brake
            outputString += "5";           
            prizm.setMotorPowers(125, 125);
            break;
        }

        case 6: {                   // 6 = Turn Left
            outputString += "6";            
            prizm.setMotorPowers(-power, power);
            break;
        }

        case 7: {                   // 7 = Turn Right
            outputString += "7";          
            prizm.setMotorPowers(power, -power);
            break;
        }

        default: {                  // Default = Error
            outputString += "ERROR";
            break;
        }
    }
}



/*================================================================================*/
/*                                  SerialEvent                                   */
/*================================================================================*/
/*  Information:     
 *      -  SerialEvent occurs whenever a new data comes in the hardware serial RX. 
 *         (Multiple bytes of data may be available to grab)
 *        
 *      -  if incoming char == '/n', we set flag so main loop can run its code
 *        
 *      -  This routine is run between each time loop() runs
 *         (so using delay() function inside the loop can delay any responses)
 *       
 * -------------------------------------------------------------------------------*/
void serialEvent() {
    while ( Serial.available() ) {
        //1. get byte + add to input string
        char inChar = (char)Serial.read();      // 1.a - grab new byte
        inputString += inChar;                  // 1.b - concat it to the inputString (global var)

        //2. IF the incoming character is a newline:
        if (inChar == '\n') {  stringComplete = true;   } // THEN set a flag for main loop
    }
}
