// Public libraries
#include <ESP8266WiFi.h>
#include <OneWire.h>
#include <PubSubClient.h>

// Private libraries
#include <Numpy.h>
#include <Blink.h>

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
char mqtt_id[] = NODE_UUID;
IPAddress broker(192,168,1,114); 
PubSubClient client(WifiClient);

// S0 configuration
#define E_PV_RESTORE 1241332                 // Wh
#define H20_RESTORE 28207                    // l
#define MS_PER_HOUR 3600000                  // ms
#define MIN_PV_DT MS_PER_HOUR / 10           // 10W minimum per ms
#define MAX_PV_DT MS_PER_HOUR / 2100         // (2kW + 5% margin = 2.1kW) maximum per ms
#define BUF_LENGTH 5
#define S0 3
long E_PV_value = E_PV_RESTORE; // Wh
float P_PV_value = 0;
float P_PV[BUF_LENGTH]; // W
int S0_prev_state = 1;
unsigned long last_pulse = millis();
const char *energy_topic = "mainhouse/energy";
const char *power_topic = "mainhouse/power";

// H20 configuration
#define H2O 2
int H2O_prev_state = 0;
float H2O_value = H20_RESTORE;
const char *H2O_topic = "mainhouse/h2o";

// I/O Variables 
#define IO_COUNT 4 // Light, Light Sensor, H2O, S0
int IO_pin[IO_COUNT] = {D0, D1, D2, D3};
int IO_pin_dir[IO_COUNT] = {OUTPUT, INPUT, INPUT, INPUT_PULLUP};

// Numpy
Numpy np;

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
void reconnect_mqtt() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect(mqtt_id)) {
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

  // Setup I/O
  for (int i = 0; i < IO_COUNT; i++) {
    pinMode(IO_pin[i], IO_pin_dir[i]);
    if (IO_pin_dir[i] == OUTPUT)
      digitalWrite(IO_pin[i], !OFF);
  }
}

void loop() {
  // Blink handling
  blink.update();

  // MQTT client connection
  if (!client.connected())  // Reconnect if connection is lost
  {
    reconnect_mqtt();
  }
  client.loop();

  // Local input handling
  H2O_read();
  S0_read(); 
}

void H2O_read(void) {
  // Initialize variables
  char charValue[MAX_LENGTH_SIGNED_INT];

  // Read I/O
  int H2O_cur_state = digitalRead(IO_pin[H2O]);
  
  // Upward flink
  if(H2O_prev_state == 0)
  {
    if (H2O_cur_state == 1)
    { // Start of pulse detected
      H2O_value += 1;
      dtostrf(H2O_value, MAX_LENGTH_SIGNED_INT, 0, charValue);
      client.publish(H2O_topic, charValue);  
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
  int S0_cur_state = digitalRead(IO_pin[S0]);

  // Compute time difference
  unsigned long delta_t_ms = millis()-last_pulse; // ms

  // Downward flank
  if(S0_prev_state == 1)
  {
    if (S0_cur_state == 0)
    { // Start of pulse detected
      E_PV_value += 1;
      dtostrf(E_PV_value, MAX_LENGTH_SIGNED_LONG, 0, charValue);
      client.publish(energy_topic, charValue);  
      if (delta_t_ms > MAX_PV_DT) // Avoid invalid power calculation
        P_PV_value = filtered_buffer(P_PV, BUF_LENGTH, MS_PER_HOUR / delta_t_ms);
      last_pulse = millis();
    }
  } 

  // If no pulse within time-out window assume
  // power below minimum power, write 0W to buffer
  if (delta_t_ms > MIN_PV_DT)
    P_PV_value = filtered_buffer(P_PV, BUF_LENGTH, 0);

  // If P_PV changed, publish it to MQTT broker
  if (P_PV_value != P_PV_prev_value) {
    dtostrf(P_PV_value, MAX_LENGTH_SIGNED_LONG, 0, charValue);
    client.publish(power_topic, charValue);   
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
