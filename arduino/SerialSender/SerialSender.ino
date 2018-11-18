#include <SoftwareSerial.h>

SoftwareSerial mySerial(2, 3); // RX, TX

void setup() {
  // Begin the Serial at 9600 Baud
  Serial.begin(9600);

  // set the data rate for the SoftwareSerial port
  mySerial.begin(4800);
}

void loop() {
  mySerial.println("Hello, world?");
  delay(1000);
}
