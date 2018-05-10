#define RAIN_PIN_IN 6
#define RAIN_PIN_OUT 7
#define RAIN_CALIBRATION 3 // ml/pulse

#define DEBUG

int prev_rain_state = HIGH;
unsigned long rain_meter = 0; // in ml

void setup() {
  #ifdef DEBUG
    // Open serial communications and wait for port to open:
    Serial.begin(9600);
    while (!Serial) {
      ; // wait for serial port to connect. Needed for native USB port only
    }
    Serial.println("Debug mode activated");
  #endif

  // Intialize pins
  pinMode(RAIN_PIN_OUT, OUTPUT);
  pinMode(RAIN_PIN_IN, INPUT_PULLUP);

  // Initialize output pin value
  digitalWrite(RAIN_PIN_OUT, LOW);   
}

void loop() {
  // Read input pin
  int cur_rain_state = digitalRead(RAIN_PIN_IN);
  if ((cur_rain_state == LOW) and (prev_rain_state == HIGH)) {
    // Start of pulse detected
    rain_meter += CALIBRATION;
    #ifdef DEBUG
      Serial.print("Rain: ");
      Serial.print(rain_meter);
      Serial.println(" ml");
    #endif
  }

  // Store current rain state for future reference
  prev_rain_state = cur_rain_state;
}
