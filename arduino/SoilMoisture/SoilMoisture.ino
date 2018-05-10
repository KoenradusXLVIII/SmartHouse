#include <SHT1x.h>

#define DEBUG

#define dataPin 10
#define clockPin 11

// Color coding on AliExpress SHT10:
// VCC - Brown
// GND - Black
// DAT - Yellow
// CLK - Blue

SHT1x sht10(dataPin, clockPin);

void setup() {
  #ifdef DEBUG
    // Open serial communications and wait for port to open:
    Serial.begin(9600);
    while (!Serial) {
      ; // wait for serial port to connect. Needed for native USB port only
    }
    Serial.println("Debug mode activated");
  #endif
}

void loop() {

  float humi = sht10.readHumidity();
  Serial.print("Humidity: ");
  Serial.println(humi);
}
