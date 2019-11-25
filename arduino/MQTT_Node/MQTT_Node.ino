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

#define IO_COUNT 0
int IO_ID[IO_COUNT] = {};
int IO_pin[IO_COUNT] = {};
unsigned long longPrevious[IO_COUNT+1];

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
      mqtt_rssi(true);
    }
    Serial.println();
    mqtt_rssi(false);

    // Set I/O and timers
    for (int i = 0; i < IO_COUNT; i++) {
      Serial.print(F("Setting pin ["));
      Serial.print(IO_pin[i]);
      Serial.println(F("] to OUTPUT mode"));
      pinMode(IO_pin[i], OUTPUT);
      digitalWrite(IO_pin[i], LOW);
      longPrevious[i] = millis();
    }
    longPrevious[IO_COUNT] = millis();
    
    // ===================== //
    // SPECIFIC SETUP STARTS //
    // ===================== //

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

    // ============================== //
    //  SPECIFIC FUNCTION CALLS ENDS  //
    // ============================== //
  }
}

// ========================= //
// SPECIFIC FUNCTIONS STARTS //
// ========================= //

// ========================= //
//  SPECIFIC FUNCTIONS ENDS  //
// ========================= //
