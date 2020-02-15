// Public libraries
#include <Ethernet.h>
#include <PubSubClient.h>
#include <EEPROM.h>

// Private libraries
#include <Blink.h>
#include <Numpy.h>

// Local includes
#include "config.h"
#include "aliases.h"

// Specific libraries
#include <dht.h>

// Ethernet client
EthernetClient EthClient;

// MQTT client
PubSubClient mqtt_client(EthClient);

// Blink client
Blink blink(LED_BUILTIN); 

// Serial configuration
char serial_buf[SERIAL_BUF_LENGTH];
int sp;

// Numpy
Numpy np;

// ============================= //
// SPECIFIC CONFIGURATION STARTS //
// ============================= //

// IO order
#define TEMP 0
#define HUMI 1
#define DOOR_STATE 2
#define LIGHT_STATE 3
#define LIGHT_OVERRIDE 4
#define VALVE_STATE 5
#define WATER_OVERRIDE 6
#define RAIN 7
#define AMBIENT_LIGHT_STATE 8
#define CHRISTMAS 9

#define IO_COUNT 10
int IO_ID[IO_COUNT] = {3, 4, 10, 11, 17, 13, 18, 8, 91, 92};
int IO_pin[IO_COUNT] = {-1, -1, 25, 27, 29, 31, 33, 37, 45, 47};
int IO_mode[IO_COUNT] = {-1, -1, INPUT, OUTPUT, INPUT_PULLUP, OUTPUT, INPUT_PULLUP, INPUT_PULLUP, INPUT, OUTPUT};
unsigned long longPrevious[IO_COUNT+1];

// DHT sensor
#define DHT21_PIN 23  
dht DHT;
float buf_temp[BUF_LENGTH];
float buf_humi[BUF_LENGTH];

// Rain sensor
#define RAIN_CALIBRATION 3 // ml/pulse
int prev_rain_state = HIGH;           // Default to high (pull-up)
int rain_counter = 0;                 // Default to 0

// Digital I/O variables
int prev_door_state = CLOSED;         // Default to closed
int prev_valve_state = CLOSED;        // Default to close
int prev_water_override = AUTO;       // Default to auto
int prev_light_state = OFF;           // Default to off
int prev_light_override = AUTO;       // Default to auto
int prev_light_sensor = DAY;          // Default to day

// ============================= //
//  SPECIFIC CONFIGURATION ENDS  //
// ============================= //

void setup() {  
  // Setup serial connection
  Serial.begin(SERIAL_SPEED);
  Serial.print("Node running firmware version: ");
  Serial.println(OTA_VERSION); 

  // Update blink interval
  blink.set_interval(BLINK_CONFIGURED);

  // Setup Ethernet
  Serial.print("Initialize Ethernet with DHCP: ");
  byte mac[] = {0x90, 0xA2, 0xDA, 0x0E, 0xC5, 0x68};
  if (Ethernet.begin(mac) == 0) {
    Serial.println("Failed to configure Ethernet using DHCP");
  } else { 
    Serial.println(Ethernet.localIP());
  }

  // Setup MQTT broker connection
  mqtt_client.setServer(broker, port);
  mqtt_client.setCallback(callback);
  mqtt_reconnect();

  // Force upload on boot
  Serial.print(F("Initializing buffers"));
  for (int i = 0; i < BUF_LENGTH; i++)
  {
    Serial.print(F("."));
    DHT.read21(DHT21_PIN);
    np.add_to_buffer(DHT.temperature, buf_temp, BUF_LENGTH);
    np.add_to_buffer(DHT.humidity, buf_humi, BUF_LENGTH);
  }
  Serial.println();

  // Set I/O and timers
  for (int i = 0; i < IO_COUNT; i++) {
    if (IO_pin[i] > -1)
    {
      Serial.print(F("Setting pin ["));
      Serial.print(IO_pin[i]);
      Serial.print(F("] to mode "));
      Serial.println(IO_mode[i]);
      pinMode(IO_pin[i], IO_mode[i]);
      if (IO_mode[i] == OUTPUT)
        digitalWrite(IO_pin[i], LOW);
    }
    longPrevious[i] = millis();
  }
  longPrevious[IO_COUNT] = millis();
  
  // ===================== //
  // SPECIFIC SETUP STARTS //
  // ===================== //

  // Additional GND on pin 39
  pinMode(39, OUTPUT);
  digitalWrite(39, LOW); 

  // ===================== //
  //  SPECIFIC SETUP ENDS  //
  // ===================== //
}

void loop() {
  // Blink handling
  blink.update();

  // MQTT handling
  mqtt_client.loop();

  // ============================== //
  // SPECIFIC FUNCTION CALLS STARTS //
  // ============================== //

  // DHT21 handling
  DHT21();

  // Door state
  door_state();

  // Light
  light_control();
  
  // Water
  water_control();

  // Rain sensor
  rain_sensor();
  
  // ============================== //
  //  SPECIFIC FUNCTION CALLS ENDS  //
  // ============================== //
}

// ========================= //
// SPECIFIC FUNCTIONS STARTS //
// ========================= //

void DHT21()
{
  // DHT21 handling
  DHT.read21(DHT21_PIN);
  // Add to rotating buffer
  np.add_to_buffer(DHT.temperature, buf_temp, BUF_LENGTH);
  np.add_to_buffer(DHT.humidity, buf_humi, BUF_LENGTH);
  // Publish filtered mean every 1 minute
  mqtt_publish(IO_ID[TEMP], np.filt_mean(buf_temp, BUF_LENGTH, 1), TEMP, 1);  
  mqtt_publish(IO_ID[HUMI], np.filt_mean(buf_humi, BUF_LENGTH, 1), HUMI, 1);  
}

void door_state()
{
  int cur_door_state = digitalRead(IO_pin[DOOR_STATE]);
  if (prev_door_state != cur_door_state)
  {
    prev_door_state = cur_door_state;
    mqtt_publish(IO_ID[DOOR_STATE], cur_door_state); 
  }
}

void light_control(void)
{
  int cur_light_sensor = digitalRead(IO_pin[AMBIENT_LIGHT_STATE]);
  int cur_light_override = digitalRead(IO_pin[LIGHT_OVERRIDE]);
  
  if (prev_light_sensor != cur_light_sensor)
  {
    prev_light_sensor = cur_light_sensor;
    mqtt_publish(IO_ID[AMBIENT_LIGHT_STATE], cur_light_sensor); 
  }
  if (prev_light_override != cur_light_override)
  {
    prev_light_override = cur_light_override;
    mqtt_publish(IO_ID[LIGHT_OVERRIDE], cur_light_override); 
  }
}

void water_control(void)
{
  int cur_water_override = digitalRead(IO_pin[WATER_OVERRIDE]);

  if (prev_water_override != cur_water_override)
  {
    prev_water_override = cur_water_override;
    mqtt_publish(IO_ID[WATER_OVERRIDE], cur_water_override); 
  }
}

void rain_sensor(void)
{
  // Read input pin
  int cur_rain_state = digitalRead(IO_pin[RAIN]);
  if ((cur_rain_state == LOW) and (prev_rain_state == HIGH)) {
    // Start of pulse detected
    rain_counter += RAIN_CALIBRATION;
    mqtt_publish(IO_ID[RAIN], rain_counter); 
  }

  // Store current rain state for future reference
  prev_rain_state = cur_rain_state;  
}

// ========================= //
//  SPECIFIC FUNCTIONS ENDS  //
// ========================= //
