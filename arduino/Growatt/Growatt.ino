#include <SoftwareSerial.h>

SoftwareSerial GrowattSerial(D2, D1);

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  Serial.println("");
  Serial.println("Growatt Serializer...");
  GrowattSerial.begin(9600);

  const uint8_t set_interval[14] = {0x3F,0x23,0x7E,0x34,0x41,0x7E,0x32,0x59,0x31,0x35,0x30,0x30,0x23,0x3F};
  for (int i=0; i<14; i++) {
    Serial.write(set_interval[i]); 
    GrowattSerial.write(set_interval[i]);
  }

  const uint8_t start_comm[8] = {0x3F,0x23,0x7E,0x34,0x42,0x7E,0x23,0x3F};
  for (int i=0; i<14; i++) {
    Serial.write(start_comm[i]); 
    GrowattSerial.write(start_comm[i]);
  }
}

void loop() {
  // put your main code here, to run repeatedly:
  if (GrowattSerial.available())
  {
    char c = GrowattSerial.read();
    Serial.write(c);  
  }
  
  if (Serial.available())
  {
    char c = Serial.read();
    Serial.write(c);
    GrowattSerial.write(c);
  }
  
}
