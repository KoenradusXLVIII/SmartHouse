void setup() {
  Serial.begin(9600);

  // set the data rate for the SoftwareSerial port
  Serial1.begin(4800);
  Serial1.println("Hello, world?");
}

void loop() {
  if (Serial1.available()) {
    Serial.println(Serial1.read());
  }
}
