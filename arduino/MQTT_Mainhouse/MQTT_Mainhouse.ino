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
char charTopic[20];

// S0 configuration
#define E_PV_RESTORE 1456194                 // Wh
#define H20_RESTORE 33508                    // l
#define MS_PER_HOUR 3600000                  // ms
#define MIN_PV_DT MS_PER_HOUR / 10           // 10W minimum per ms
#define MAX_PV_DT MS_PER_HOUR / 2100         // (2kW + 5% margin = 2.1kW) maximum per ms
#define BUF_LENGTH 5
#define S0_pin D0
#define E_PV_ID 47
#define P_PV_ID 6
long E_PV_value = E_PV_RESTORE; // Wh
float P_PV_value = 0;
float P_PV[BUF_LENGTH]; // W
int S0_prev_state = 1;
unsigned long last_pulse = millis();

// H20 configuration
#define H2O_pin D1
#define H2O_ID 7
int H2O_prev_state = 0;
float H2O_value = H20_RESTORE;

// Numpy
Numpy np;

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
  mqtt_client.setServer(broker, 1883);

  // Extract node UUID
  byte mac[6];
  WiFi.macAddress(mac);
  array_to_string(mac, 6, node_uuid);

  // Setup I/O
  pinMode(S0_pin, INPUT);
  pinMode(H2O_pin, INPUT_PULLUP);
}

void loop() {
  // Blink handling
  blink.update();

  // Local input handling
  H2O_read();
  S0_read(); 

  // MQTT
  mqtt_client.loop();

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


void mqtt_publish(int id, float value) {
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
  dtostrf(value, 3, 0, charValue);

  Serial.print("MQTT upload on topic: ");
  Serial.print(charTopic);
  Serial.print(" => ");
  Serial.println(charValue);
  mqtt_client.publish(charTopic, charValue, true);  
}

// Read H2O sensor
// Pulls input to GND on pulse
void H2O_read(void) {
  // Read I/O
  int H2O_cur_state = digitalRead(H2O_pin);
  
  // Upward flink
  if(H2O_prev_state == 0)
  {
    if (H2O_cur_state == 1)
    { // Start of pulse detected
      H2O_value += 1;
      mqtt_publish(H2O_ID, H2O_value);  
    }
  }

  H2O_prev_state = H2O_cur_state;
}

void S0_read(void) {
  // Initialize variables
  char charValue[MAX_LENGTH_SIGNED_LONG];
  
  // Store current P_PV
  float P_PV_prev_value = np.filt_mean(P_PV, BUF_LENGTH, 1); ;
  
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
      mqtt_publish(E_PV_ID, E_PV_value);  
      if (delta_t_ms > MAX_PV_DT) // Avoid invalid power calculation
        P_PV_value = filtered_buffer(P_PV, BUF_LENGTH, MS_PER_HOUR / delta_t_ms);
      last_pulse = millis();
    }
  } 

  // If no pulse within time-out window assume
  // power below minimum power, write 0 to buffer
  if (delta_t_ms > MIN_PV_DT)
    P_PV_value = filtered_buffer(P_PV, BUF_LENGTH, 0);

  // If P_PV changed, publish it to MQTT broker
  if (P_PV_value != P_PV_prev_value) {
    mqtt_publish(P_PV_ID, P_PV_value);    
  }
  
  // Store current S0 state for future reference
  S0_prev_state = S0_cur_state;
}

float filtered_buffer(float *buf_data, float buf_length, float value) {
  // Shift buffer
  for (int n = (buf_length - 1); n > 0; n--) {
    buf_data[n] = buf_data[n - 1];
  }

  // Return filtered mean (1 stdev)
  return np.filt_mean(buf_data, buf_length, 1); 
}
