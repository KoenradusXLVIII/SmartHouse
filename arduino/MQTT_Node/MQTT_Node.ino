// Public libraries
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <EEPROM.h>

// Private libraries
#include <Blink.h>
#include <Numpy.h>

// Local includes
#include "config.h"
#include "aliases.h"

// Specific libraries

// WiFi client configuration
char ssid[MAX_WIFI_LENGTH];
char pass[MAX_WIFI_LENGTH];
WiFiClient WifiClient;
int prev_rssi = 0;
int rssi_buf[BUF_LENGTH];

// Blink configuration
Blink blink(LED_BUILTIN); 

// MQTT configuration
PubSubClient mqtt_client(WifiClient);
char node_uuid[12];
char charTopic[20];

// Serial configuration
char serial_buf[SERIAL_BUF_LENGTH];
int sp;

// Numpy
Numpy np;

// EEPROM
bool EEPROM_initialized = false;

// Global timing
unsigned long longPrevious = millis();

// ============================= //
// SPECIFIC CONFIGURATION STARTS //
// ============================= //

#define IO_COUNT 0
int IO_ID[IO_COUNT] = {};
int IO_pin[IO_COUNT] = {};

// ============================= //
//  SPECIFIC CONFIGURATION ENDS  //
// ============================= //

void setup() {  
  // Setup serial connection
  Serial.begin(SERIAL_SPEED);
  Serial.println(F("."));

  // Extract node UUID
  byte mac[6];
  WiFi.macAddress(mac);
  array_to_string(mac, 6, node_uuid);

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

    // Setup MQTT broker connection
    mqtt_client.setServer(broker, port);
    mqtt_client.setCallback(callback);

    // Subscribe to my MQTT topic
    strcpy(charTopic, "nodes/");
    strcat(charTopic, node_uuid);
    strcat(charTopic, "/io/#");
    mqtt_client.subscribe(charTopic);
    
  } else {   
    // Node not configured for WiFi
    Serial.println(F("Node not configured"));
    
    // Update blink interval
    blink.set_interval(BLINK_UNCONFIGURED);

    // Initialise serial interface for read
    reset_serial_buffer();

    // ===================== //
    // SPECIFIC SETUP STARTS //
    // ===================== //

    // ===================== //
    //  SPECIFIC SETUP ENDS  //
    // ===================== //
  }
}

void loop() {
  // Blink handling
  blink.update();

  // Listen on serial port
  listen_serial();
    
  if (EEPROM_initialized)
  { // If node is configured...
    // Handle MQTT traffic
    mqtt_client.loop();

    // Report RSSI
    mqtt_rssi();

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
