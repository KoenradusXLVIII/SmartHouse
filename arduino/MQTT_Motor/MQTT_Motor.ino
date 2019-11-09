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

// Initial setup
void setup() {
  // Setup serial connection
  Serial.begin(9600);

  // Setup WiFi
  setup_wifi();

  // Setup MQTT broker connection
  mqtt_client.setServer(broker, 1883);
  mqtt_client.setCallback(callback);

  // Extract node UUID
  byte mac[6];
  WiFi.macAddress(mac);
  array_to_string(mac, 6, node_uuid);

  // Subscribe to my MQTT topic
  char charTopic[20];
  strcpy(charTopic, "nodes/");
  //strcat(charTopic, node_uuid);
  strcat(charTopic, "3C71BF315A37");
  strcat(charTopic, "/#");
  if (!mqtt_client.connected())  // Reconnect if connection is lost
    mqtt_reconnect();
  mqtt_client.subscribe(charTopic);
  Serial.print("Subscribing to topic: ");
  Serial.println(charTopic);
}

// MQTT callback triggered on message received
void callback(char* topic, byte* payload, unsigned int length) {
  int intValue;
  char charPayload[length];

  for (int i = 0; i < length; i++)
    charPayload[i] = (char)payload[i];

  sscanf(charPayload, "%d", &intValue);
  process_cmd(sensor_id(topic), intValue);
}

// Control IO based on MQTT command
void process_cmd(int intSensorID, int intValue) {
  for (int i = 0; i < IO_COUNT; i++) {
    if (IO_ID[i] == intSensorID)
      digitalWrite(IO_PIN[i], !intValue);
  }
}

// Extract sensor ID from topic
int sensor_id(char* topic) {
  int intSensorID;

  for (int i = 0; i < strlen(topic); i++ )
    if (topic[i] == '/')
      topic[i] = ' ';

  sscanf(topic, "%*s %*s %d", &intSensorID);

  return intSensorID;
}

// Main loop
void loop() {
  // Blink handling
  blink.update();

  // MQTT
  mqtt_publish(TEMP_SENSOR_ID, temp);
  mqtt_client.loop();
}

// Extrac MAC to string
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
    // Attempt to connect
    if (mqtt_client.connect(node_uuid, MQTT_USER, MQTT_API_KEY)) {
    } else {
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

// Publish once every x minutes
void mqtt_publish(int id, float value) {
  unsigned long longNow = millis();
  
  if (longNow - longPrevious >= (UPLOAD_RATE*60000)) {
    // Reset ticker
    longPrevious = longNow;

    // MQTT client connection
    if (!mqtt_client.connected())  // Reconnect if connection is lost
      mqtt_reconnect();
      
    // Parse topic and value data
    char charTopic[TOPIC_LENGTH];
    char charID[MAX_LENGTH_SIGNED_INT];
    char charValue[6];
    strcpy(charTopic, "nodes/");
    strcat(charTopic, node_uuid);
    strcat(charTopic, "/");
    itoa(id, charID, 10);
    strcat(charTopic, charID);
    dtostrf(value, 3, 2, charValue);

    // Publish value
    mqtt_client.publish(charTopic, charValue, true);  
  }
}
