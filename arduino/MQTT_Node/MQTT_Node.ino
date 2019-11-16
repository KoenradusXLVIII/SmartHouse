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
float buf_rssi[BUF_LENGTH];
long prev_rssi = 0;

// Blink configuration
Blink blink(LED_BUILTIN, 1000);     // Blink every second   

// MQTT configuration
#define TOPIC_LENGTH 64
PubSubClient mqtt_client(WifiClient);
char node_uuid[12];

// DS18B20
OneWire  ds(D2);  // on pin D2
byte addr[8] = {0x28, 0xE0, 0xC4, 0x19, 0x17, 0x13, 0x01, 0x76};
float calibration = 2.0;
float buf_temp[BUF_LENGTH];

// Numpy
Numpy np;

// Nebula configuration
#define TEMP_SENSOR_ID 85
#define IO_COUNT 2
int IO_ID[IO_COUNT] = {19, 90};
int IO_PIN[IO_COUNT] = {D0, D1};

// Global timing
#define UPLOAD_RATE 1                                             // Upload every x minutes
unsigned long longPrevious = millis() - (UPLOAD_RATE*60000);      // Force upload on boot

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
  mqtt_client.setServer(broker, port);
  mqtt_client.setCallback(callback);

  // Extract node UUID
  byte mac[6];
  WiFi.macAddress(mac);
  array_to_string(mac, 6, node_uuid);

  // Subscribe to my MQTT topic
  char charTopic[20];
  strcpy(charTopic, "nodes/");
  strcat(charTopic, node_uuid);
  strcat(charTopic, "/#");
  if (!mqtt_client.connected())  // Reconnect if connection is lost
    mqtt_reconnect();
  mqtt_client.subscribe(charTopic);
  Serial.print("Subscribing to topic: ");
  Serial.println(charTopic);

  // Fill buffers
  Serial.print(F("Initializing buffers"));
  for (int i = 0; i<BUF_LENGTH; i++)
  {
    float temp = read_filtered_DS18B20(buf_temp, BUF_LENGTH, addr);  
    long rssi = read_filtered_RSSI(buf_rssi, BUF_LENGTH);
    Serial.print(F("."));
  }
  Serial.println(F(""));
}

void callback(char* topic, byte* payload, unsigned int length) {
  int intValue;
  char charPayload[length];

  for (int i = 0; i < length; i++)
    charPayload[i] = (char)payload[i];

  sscanf(charPayload, "%d", &intValue);

  process_cmd(sensor_id(topic), intValue);
 
  Serial.print("Message for sensor: ");
  Serial.print(sensor_id(topic));
  Serial.print(" => ");
  Serial.println(intValue); 
}


void process_cmd(int intSensorID, int intValue) {
  for (int i = 0; i < IO_COUNT; i++) {
    if (IO_ID[i] == intSensorID)
      digitalWrite(IO_PIN[i], !intValue);
  }
}

int sensor_id(char* topic) {
  int intSensorID;

  for (int i = 0; i < strlen(topic); i++ )
    if (topic[i] == '/')
      topic[i] = ' ';

  sscanf(topic, "%*s %*s %d", &intSensorID);

  return intSensorID;
}

void loop() {
  // Blink handling
  blink.update();

  // DS18B20
  float temp = read_filtered_DS18B20(buf_temp, BUF_LENGTH, addr);

  // MQTT
  mqtt_publish(TEMP_SENSOR_ID, temp);
  mqtt_publish_rssi();
  mqtt_client.loop();

}

void mqtt_publish_rssi(void)
{ 
  long rssi = read_filtered_RSSI(buf_rssi, BUF_LENGTH);
  
  if (prev_rssi != rssi) {
    prev_rssi = rssi;
    // MQTT client connection
    if (!mqtt_client.connected())  // Reconnect if connection is lost
      mqtt_reconnect();
      
    // Publish value
    char charTopic[TOPIC_LENGTH];
    char charValue[3];
    strcpy(charTopic, "nodes/");
    strcat(charTopic, node_uuid);
    strcat(charTopic, "/rssi");
    itoa(rssi, charValue, 10);

    Serial.print("MQTT upload of RSSI: ");
    Serial.println(charValue);
    mqtt_client.publish(charTopic, charValue, true);    
  }
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
      Serial.println(" connected");
    } else {
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}


void mqtt_publish(int id, float value) {
  unsigned long longNow = millis();
  
  if (longNow - longPrevious >= (UPLOAD_RATE*60000)) {
    // Reset ticker
    longPrevious = longNow;

    // MQTT client connection
    if (!mqtt_client.connected())  // Reconnect if connection is lost
      mqtt_reconnect();
      
    // Publish value
    char charTopic[TOPIC_LENGTH];
    char charID[MAX_LENGTH_SIGNED_INT];
    char charValue[6];
    strcpy(charTopic, "nodes/");
    strcat(charTopic, node_uuid);
    strcat(charTopic, "/");
    itoa(id, charID, 10);
    strcat(charTopic, charID);
    dtostrf(value, 1, 2, charValue);

    Serial.print("MQTT upload of temperature: ");
    Serial.println(charValue);
    mqtt_client.publish(charTopic, charValue, true);  
  }
}

long read_filtered_RSSI(float *buf_data, int buf_length) {
  // Shift buffer
  for (int n = (buf_length - 1); n > 0; n--) {
    buf_data[n] = buf_data[n - 1];
  }

  // Append new data
  buf_data[0] = WiFi.RSSI();

  // Return filtered mean (1 stdev)
  return (long) np.filt_mean(buf_data, buf_length, 1);
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
