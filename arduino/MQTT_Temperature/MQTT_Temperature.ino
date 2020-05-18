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
int IO_ID[IO_COUNT] = {0};
int IO_pin[IO_COUNT] = {0};
unsigned long longPrevious[IO_COUNT+1];

// DS18B20
#define TEMP 0
OneWire  ds(D2);  // on pin D2
byte addr[8]; // {0x28, 0x61, 0x64, 0x11, 0xA9, 0x99, 0x20, 0x79}
float calibration = 4.0;
float temp_buf[BUF_LENGTH];

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

    // Set DS18B20 address
    getDeviceAddress(addr);

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
      np.add_to_buffer(DS18B20_read(addr), temp_buf, BUF_LENGTH);
    }
    Serial.println();
    mqtt_rssi(false);
    mqtt_temp(false);    

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

    mqtt_temp(true); 

    // ============================== //
    //  SPECIFIC FUNCTION CALLS ENDS  //
    // ============================== //
  }
}

// ========================= //
// SPECIFIC FUNCTIONS STARTS //
// ========================= //

// Read temperature sensors
void mqtt_temp(bool timed) {
  np.add_to_buffer(DS18B20_read(addr), temp_buf, BUF_LENGTH);
  if (timed)
    mqtt_publish(IO_ID[TEMP], np.filt_mean(temp_buf, BUF_LENGTH, 1), 1);  
  else
    mqtt_publish(IO_ID[TEMP], np.filt_mean(temp_buf, BUF_LENGTH, 1));  
}

void getDeviceAddress(byte * addr) {
  byte i;

  /* initiate a search for the OneWire object we created and read its value into
  addr array we declared above*/
  
  while(ds.search(addr)) {
    Serial.print("DS18B20 address: ");
    //read each byte in the address array
    for( i = 0; i < 8; i++) {
      Serial.print("0x");
      if (addr[i] < 16) {
        Serial.print('0');
      }
      // print each byte in the address array in hex format
      Serial.print(addr[i], HEX);
      if (i < 7) {
        Serial.print(" ");
      }
    }
    // a check to make sure that what we read is correct.
    if ( OneWire::crc8( addr, 7) != addr[7]) {
        Serial.print("CRC is not valid!\n");
        return;
    }
  }
  ds.reset_search();
  Serial.println("");
}

float DS18B20_read(byte * addr){
 byte data[12];
 float celsius;

 ds.reset();
 ds.select(addr);
 ds.write(0x44, 1); // Start conversion
 delay(1000);

 ds.reset();
 ds.select(addr);
 ds.write(0xBE); // Read scratchpad

 for (int i=0; i<9; i++) {
  data[i] = ds.read();
 }

 OneWire::crc8(data,8);
 
 int16_t raw = (data[1] << 8) | data[0];
 celsius = (float)raw / 16.0;

 return celsius-calibration;
}

// ========================= //
//  SPECIFIC FUNCTIONS ENDS  //
// ========================= //
