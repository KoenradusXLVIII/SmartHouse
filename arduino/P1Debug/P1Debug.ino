#include <AltSoftSerial.h>

AltSoftSerial altSerial;

void setup() {
  Serial.begin(115200);
  Serial.println("AltSoftSerial Test Begin");
  altSerial.begin(115200);
}

void loop() {
  char c;

  if (altSerial.available()) {
    c = altSerial.read();
    Serial.print(c);
  }
}
