// Public libraries
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <EEPROM.h>
#include <ArduinoOTA.h>
#include <ESP8266httpUpdate.h>
#include <Adafruit_NeoPixel.h>

// Private libraries
#include <Blink.h>
#include <Numpy.h>

// Local includes
#include "config.h"
#include "aliases.h"

// Specific libraries
#include <OneWire.h>

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

#define IO_COUNT 1
int IO_ID[IO_COUNT] = {4};
int IO_pin[IO_COUNT] = {4};
unsigned long longPrevious[IO_COUNT+1];

Adafruit_NeoPixel pixel(1, IO_pin[0], NEO_GRB + NEO_KHZ800);
int rainbow[7][3] = {{255, 0, 0}, {255, 127, 0}, {255, 255, 0}, {0, 255, 0}, {0, 0, 255}, {46, 43, 95}, {139, 0, 255}};
int rainbow_itt = 0;

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
    //blink.set_interval(BLINK_CONFIGURED);
    digitalWrite(LED_BUILTIN, HIGH);
    
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

    // ===================== //
    // SPECIFIC SETUP STARTS //
    // ===================== //

    pixel.begin();
    pixel.clear();

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

    // Set I/O and timers
    for (int i = 0; i < IO_COUNT; i++) {
      pinMode(IO_pin[i], OUTPUT);
      digitalWrite(IO_pin[i], LOW);
      longPrevious[i] = millis();
    }
    longPrevious[IO_COUNT] = millis();
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
    
    unsigned long longNow = millis();
    if (longNow - longPrevious[0] >= 1000) {
      // Reset ticker
      longPrevious[0] = longNow;
      pixel.setPixelColor(0, pixel.Color(rainbow[rainbow_itt][0], rainbow[rainbow_itt][1], rainbow[rainbow_itt][2]));
      pixel.show();   // Send the updated pixel colors to the hardware.
      if (rainbow_itt < 7)
        rainbow_itt += 1;
      else
        rainbow_itt = 0;
    }

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
