// Public libraries
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <EEPROM.h>
#include <ArduinoOTA.h>
#include <ESP8266httpUpdate.h>

// Private libraries
#include <Blink.h>
#include <Numpy.h>

// Local includes
#include "config.h"
#include "aliases.h"

// Specific libraries

// WiFi client
WiFiClient WifiClient;

// MQTT client
PubSubClient mqtt_client(WifiClient);

// Blink client
Blink blink(LED_BUILTIN); 

// Serial configuration
char serial_buf[SERIAL_BUF_LENGTH];
int sp;

// Numpy
Numpy np;

// EEPROM
bool EEPROM_initialized = false;

// ============================= //
// SPECIFIC CONFIGURATION STARTS //
// ============================= //

// IO order
#define POWER 0
#define ENERGY 1
#define WATER 2

#define IO_COUNT 3
int IO_ID[IO_COUNT] = {6, 47, 7};
int IO_pin[IO_COUNT] = {-1, -1, -1};
unsigned long longPrevious[IO_COUNT+1];

// S0 configuration
#define E_PV_RESTORE 1485488                 // Wh
#define H20_RESTORE 34909                    // l
#define MS_PER_HOUR 3600000                  // ms
#define MIN_PV_DT MS_PER_HOUR / 10           // 10W minimum per ms
#define MAX_PV_DT MS_PER_HOUR / 2100         // (2kW + 5% margin = 2.1kW) maximum per ms
#define BUF_LENGTH 5
#define S0_pin D3                            // Has to have pullup!
int E_PV_value = E_PV_RESTORE; // Wh
int P_PV_value = 0;
int P_PV[BUF_LENGTH]; // W
int S0_prev_state = 1;
unsigned long last_pulse = millis();

// H20 configuration
#define H2O_pin D1
int H2O_prev_state = 0;
int H2O_value = H20_RESTORE;

// ============================= //
//  SPECIFIC CONFIGURATION ENDS  //
// ============================= //

void setup() {  
  // Setup serial connection
  Serial.begin(SERIAL_SPEED);
  Serial.print("Node running firmware version: ");
  Serial.println(OTA_VERSION); 

  // Initialise EEPROM
  EEPROM.begin(EEPROM_SIZE); 
  EEPROM_initialized = check_EEPROM_init();
  if (EEPROM_initialized)
  { // If node is configured...
    Serial.println(F("Node configured, initializing..."));
    // Update blink interval
    blink.set_interval(BLINK_CONFIGURED);
    
    // Setup WiFi
    setup_WiFi();
    set_uuid();

    // Setup OTA
    setup_OTA();

    // Setup MQTT broker connection
    mqtt_client.setServer(broker, port);
    mqtt_client.setCallback(callback);
    mqtt_reconnect();

    // Force upload on boot
    Serial.print(F("Initializing buffers"));
    for (int i = 0; i < BUF_LENGTH; i++)
    {
      Serial.print(F("."));
      np.add_to_buffer(0, P_PV, BUF_LENGTH);
      mqtt_rssi(true);
    }
    Serial.println();
    mqtt_rssi(false);
    mqtt_ssid();

    // Set I/O and timers
    for (int i = 0; i < IO_COUNT; i++) {
      if (IO_pin[i] > -1)
      {
        Serial.print(F("Setting pin ["));
        Serial.print(IO_pin[i]);
        Serial.println(F("] to OUTPUT mode"));
        pinMode(IO_pin[i], OUTPUT);
        digitalWrite(IO_pin[i], LOW);
      }
      longPrevious[i] = millis();
    }
    longPrevious[IO_COUNT] = millis();
    
    // ===================== //
    // SPECIFIC SETUP STARTS //
    // ===================== //

    // Setup I/O
    pinMode(S0_pin, INPUT_PULLUP);
    pinMode(H2O_pin, INPUT);
  
    // Set up additional GND
    pinMode(D2, OUTPUT);
    digitalWrite(D2, LOW);

    // ===================== //
    //  SPECIFIC SETUP ENDS  //
    // ===================== //
    
  } else {   
    // Node not configured for WiFi
    Serial.println(F("Node not configured"));
    
    // Update blink interval
    blink.set_interval(BLINK_UNCONFIGURED);

    // Initialise serial interface for read
    reset_serial_buffer();
  }
}

void loop() {
  // Blink handling
  blink.update();

  // Handle serial traffic
  listen_serial();
    
  if (EEPROM_initialized)
  { // If node is configured...
    // Handle MQTT traffic
    mqtt_client.loop();

    // Report RSSI
    mqtt_rssi(true);

    // ============================== //
    // SPECIFIC FUNCTION CALLS STARTS //
    // ============================== //

    H2O_read();
    S0_read(); 

    // ============================== //
    //  SPECIFIC FUNCTION CALLS ENDS  //
    // ============================== //
  }
}

// ========================= //
// SPECIFIC FUNCTIONS STARTS //
// ========================= //

// Read H2O sensor
// Pulls input to GND on pulse
void H2O_read(void) {
  // Read I/O
  int H2O_cur_state = digitalRead(H2O_pin);
  
  // Upward flank
  if(H2O_prev_state == 0)
  {
    if (H2O_cur_state == 1)
    { // Start of pulse detected
      H2O_value += 1;
      mqtt_publish(IO_ID[WATER], H2O_value);  
    }
  }

  H2O_prev_state = H2O_cur_state;
}

void S0_read(void) {
  // Initialize variables
  char charValue[MAX_LENGTH_SIGNED_LONG];
  
  // Read input pin
  int S0_cur_state = digitalRead(S0_pin);

  // Compute time difference
  unsigned long delta_t_ms = millis()-last_pulse; // ms

  // Downward flank
  if(S0_prev_state == 1)  
  {
    if (S0_cur_state == 0)
    { // Start of pulse detected
      E_PV_value += 1;
      mqtt_publish(IO_ID[ENERGY], E_PV_value);  
      if (delta_t_ms > MAX_PV_DT) // Avoid invalid power calculation
      {
          np.add_to_buffer(MS_PER_HOUR / delta_t_ms, P_PV, BUF_LENGTH);
          P_PV_value = np.filt_mean(P_PV, BUF_LENGTH, 1);
          mqtt_publish(IO_ID[POWER], P_PV_value);  
      }
      last_pulse = millis();
    }
  } 

  // If no pulse within time-out window assume
  // power below minimum power, write 0s to buffer
  if ((delta_t_ms > MIN_PV_DT) && (np.filt_mean(P_PV, BUF_LENGTH, 1) > 0)) {
    Serial.println("No pulse in time-out, clearing buffer...");
    for (int i = 0; i < BUF_LENGTH; i++)
      np.add_to_buffer(0, P_PV, BUF_LENGTH);
    mqtt_publish(IO_ID[POWER], 0);
  }
  
  // Store current S0 state for future reference
  S0_prev_state = S0_cur_state;
}    

// ========================= //
//  SPECIFIC FUNCTIONS ENDS  //
// ========================= //
