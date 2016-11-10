#include <AltSoftSerial.h>
// AltSoftSerial always uses these pins:
//
// Board          Transmit  Receive   PWM Unusable
// -----          --------  -------   ------------
// Teensy 2.0         9        10       (none)
// Teensy++ 2.0      25         4       26, 27
// Arduino Uno        9         8         10
// Arduino Mega      46        48       44, 45
// Wiring-S           5         6          4
// Sanguino          13        14         12

#define BUFSIZE 75

AltSoftSerial altSerial;
char c;
char buffer[BUFSIZE];
int bufpos = 0;

void setup() {
    Serial.begin(115200);
    altSerial.begin(115200);
    pinMode(2,OUTPUT);
    digitalWrite(2, HIGH);
}

void loop() {
    if (altSerial.available()) {
        c = altSerial.read();
        buffer[bufpos] = c;
        bufpos++;

        if(c == '\n') { // End of line detected
          Serial.print(buffer);
          if(buffer[0] == '!') // End of telegram detected
            Serial.println("0-1:24.2.1(01000.1234*kWh)");
          for (int i=0; i<BUFSIZE; i++)
            buffer[i] = 0;
          bufpos = 0;
        }
    }
}
