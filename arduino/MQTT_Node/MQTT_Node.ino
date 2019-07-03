// Public libraries
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <OneWire.h>

// Private libraries
#include <Blink.h>
#include <Numpy.h>

// Local includes
#include "config.h"
#include "aliases.h"

// WiFi client configuration
char ssid[] = WIFI_SSID;
char pass[] = WIFI_PASSWD;
WiFiClient WifiClient;

// Blink configuration
Blink blink(LED_BUILTIN, 1000);     // Blink every second   

// MQTT configuration
#define TOPIC_LENGTH 64
PubSubClient mqtt_client(WifiClient);
char node_uuid[12];

// DS18B20
#define BUF_LENGTH 32
OneWire  ds(D2);  // on pin D2
byte addr[8] = {0x28, 0xE0, 0xC4, 0x19, 0x17, 0x13, 0x01, 0x76};
float calibration = 2.0;
float buf_temp[BUF_LENGTH];

// Numpy
Numpy np;

// Nebula configuration
#define TEMP_SENSOR_ID 85

// Global timing
#define UPLOAD_RATE 5               // Upload every 5 minutes
unsigned long longPrevious = 0;  

// Connect to WiFi network
void setup_wifi() {
  // Report SSID
  Serial.print(F("Connecting to: "));
  Serial.print(ssid);
  Serial.print(F(" "));

  // Connect to WiFi network
  WiFi.mode(WIFI_STA);
  WiFi.config(ip, gateway, subnet, dns);
  WiFi.begin(ssid, pass);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(F("."));
  }

  // Report the IP address
  Serial.println(F(""));
  Serial.print(F("IP Address: "));
  Serial.println(WiFi.localIP());
  Serial.print("MAC: ");
  Serial.println(WiFi.macAddress());
}

void setup() {
  // Setup serial connection
  Serial.begin(9600);

  // Setup WiFi
  setup_wifi();

  // Setup MQTT broker connection
  byte mac[6];
  mqtt_client.setServer(broker, 1883);
  WiFi.macAddress(mac);
  array_to_string(mac, 6, node_uuid);
}

void loop() {
  // Blink handling
  blink.update();

  // DS18B20
  float temp = read_filtered_DS18B20(buf_temp, BUF_LENGTH, addr);

  // MQTT
  mqtt_interval(TEMP_SENSOR_ID, temp);

}

void array_to_string(byte array[], unsigned int len, char buffer[])
{
    for (unsigned int i = 0; i < len; i++)
    {
        byte nib1 = (array[i] >> 4) & 0x0F;
        byte nib2 = (array[i] >> 0) & 0x0F;
        buffer[i*2+0] = nib1  < 0xA ? '0' + nib1  : 'A' + nib1  - 0xA;
        buffer[i*2+1] = nib2  < 0xA ? '0' + nib2  : 'A' + nib2  - 0xA;
    }
    buffer[len*2] = '\0';
}

// Reconnect to client
void mqtt_reconnect() {
  // Loop until we're reconnected
  while (!mqtt_client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (mqtt_client.connect(node_uuid, MQTT_USER, MQTT_API_KEY)) {
      Serial.println("connected");
    } else {
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}


void mqtt_interval(int id, float value) {
  unsigned long longNow = millis();
  
  if (longNow - longPrevious >= (UPLOAD_RATE*1000)) {
    // Reset ticker
    longPrevious = longNow;

    // MQTT client connection
    if (!mqtt_client.connected())  // Reconnect if connection is lost
    {
      mqtt_reconnect();
    }
    mqtt_client.loop();

    // Publish value
    char charTopic[TOPIC_LENGTH];
    char charID[MAX_LENGTH_SIGNED_INT];
    char charValue[6];
    strcpy(charTopic, "nodes/");
    strcat(charTopic, node_uuid);
    strcat(charTopic, "/");
    itoa(id, charID, 10);
    strcat(charTopic, charID);
    dtostrf(value, 3, 2, charValue);
    mqtt_client.publish(charTopic, charValue);  
  }
}

float read_filtered_DS18B20(float *buf_data, int buf_length, byte *addr) {
  // Shift buffer
  for (int n = (buf_length - 1); n > 0; n--) {
    buf_data[n] = buf_data[n - 1];
  }

  // Append new data
  buf_data[0] = _DS18B20_read(addr);

  // Return filtered mean (1 stdev)
  return np.filt_mean(buf_data, buf_length, 1);
}

float _DS18B20_read(byte * addr){
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
