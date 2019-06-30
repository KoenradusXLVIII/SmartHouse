// Public libraries
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// Private libraries
#include <Blink.h>

// Local includes
#include "config.h"

// WiFi client configuration
char ssid[] = WIFI_SSID;
char pass[] = WIFI_PASSWD;
WiFiClient WifiClient;

// MQTT configuration
const char *ID = "WemosLivingRoom";  // Name of our device, must be unique
const char *temp_topic = "mainhouse/temp";  // Topic to subcribe to
const char *power_topic = "mainhouse/power";  // Topic to subcribe to
IPAddress broker(192,168,1,114); // IP address of your MQTT broker eg. 192.168.1.50
PubSubClient client(WifiClient); // Setup MQTT client
unsigned long longPrevious = 0;  

// Blink configuration
Blink blink(LED_BUILTIN, 1000);     // Blink every second       

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
}

// Reconnect to client
void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect(ID)) {
      Serial.println("connected");

    } else {
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

void setup() {
  // Setup serial connection
  Serial.begin(9600);

  // Setup WiFi
  setup_wifi();

  // Setup MQTT broker connection
  client.setServer(broker, 1883);
}

void loop() {

  // Blink handling
  blink.update();

  // MQTT client connection
  if (!client.connected())  // Reconnect if connection is lost
  {
    reconnect();
  }
  client.loop();

  // MQTT publish data
  unsigned long longNow = millis();
  if (longNow - longPrevious >= 5000) {
    longPrevious = longNow;
    client.publish(temp_topic, "25");
    client.publish(power_topic, "100");
  }    
}
