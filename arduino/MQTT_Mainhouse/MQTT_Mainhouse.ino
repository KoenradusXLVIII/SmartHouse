// Public libraries
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <OneWire.h>
#include <EEPROM.h>

// Private libraries
#include <Blink.h>
#include <Numpy.h>

// Local includes
#include "config.h"
#include "aliases.h"

// WiFi client configuration
char ssid[MAX_WIFI_LENGTH];
char pass[MAX_WIFI_LENGTH];
WiFiClient WifiClient;

// Blink configuration
#define BLINK_UNCONFIGURED 2000
#define BLINK_CONFIGURED 1000
Blink blink(LED_BUILTIN); 

// MQTT configuration
#define TOPIC_LENGTH 64
PubSubClient mqtt_client(WifiClient);
char node_uuid[12];
char charTopic[20];

// S0 configuration
#define E_PV_RESTORE 1458230                 // Wh
#define H20_RESTORE 33671                    // l
#define MS_PER_HOUR 3600000                  // ms
#define MIN_PV_DT MS_PER_HOUR / 10           // 10W minimum per ms
#define MAX_PV_DT MS_PER_HOUR / 2100         // (2kW + 5% margin = 2.1kW) maximum per ms
#define BUF_LENGTH 5
#define S0_pin D3                            // Has to have pullup!
#define E_PV_ID 47
#define P_PV_ID 6
int E_PV_value = E_PV_RESTORE; // Wh
int P_PV_value = 0;
int P_PV[BUF_LENGTH]; // W
int S0_prev_state = 1;
unsigned long last_pulse = millis();

// H20 configuration
#define H2O_pin D1
#define H2O_ID 7
int H2O_prev_state = 0;
float H2O_value = H20_RESTORE;

// Serial configuration
#define SERIAL_SPEED 9600
#define SERIAL_BUF_LENGTH 32
char serial_buf[SERIAL_BUF_LENGTH];
int sp;

// Numpy
Numpy np;

// Connect to WiFi network
bool setup_WiFi() {
  int i = 0;
  
  // Report SSID
  Serial.print(F("Connecting to: "));
  Serial.print(ssid);
  Serial.print(F(" "));

  // Connect to WiFi network
  WiFi.mode(WIFI_STA);
  //WiFi.config(ip, gateway, subnet, dns);
  WiFi.begin(ssid, pass);
  
  while ((WiFi.status() != WL_CONNECTED) and (i < MAX_WIFI_WAITS)) {
    delay(WIFI_WAIT);
    //Serial.print(F("."));
    i++;
  }

  if (WiFi.status() != WL_CONNECTED)
    return false;

  // Extract node UUID
  byte mac[6];
  WiFi.macAddress(mac);
  array_to_string(mac, 6, node_uuid);

  // Report the IP address
  Serial.println(F(""));
  Serial.print(F("IP Address: "));
  Serial.println(WiFi.localIP());
  Serial.print(F("MAC: "));
  Serial.println(WiFi.macAddress());

  return true;
}

void setup() {
  // Setup serial connection
  Serial.begin(SERIAL_SPEED);

  // Initialise EEPROM
  EEPROM.begin(EEPROM_SIZE);

  if (check_EEPROM_init())
  { // If node is configured...
    // Update blink interval
    blink.set_interval(BLINK_CONFIGURED);
    
    // Setup WiFi
    setup_WiFi();

    // Setup MQTT broker connection
    mqtt_client.setServer(broker, port);
  } else {
    // Node not configured for WiFi
    // Update blink interval
    blink.set_interval(BLINK_UNCONFIGURED);
    
    // Setup I/O
    pinMode(S0_pin, INPUT_PULLUP);
    pinMode(H2O_pin, INPUT);
  
    // Set up additional GND
    pinMode(D2, OUTPUT);
    digitalWrite(D2, LOW);

    // Initialise serial interface for read
    reset_serial_buffer();
  }
}

void loop() {
  // Blink handling
  blink.update();

  if (check_EEPROM_init())
  { // If node is configured...
    // Local input handling
    H2O_read();
    S0_read(); 

    // MQTT
    mqtt_client.loop();
  } else {
    // Wait for configuration from Python
    listen_serial();
  }
}

void reset_serial_buffer(void)
{
  sp = 0;
  for(int i=0; i<SERIAL_BUF_LENGTH; i++)
  { // Initialize serial buffer
    serial_buf[i] = '\0';
  }
}

void listen_serial(void)
{
  char c;
  while(Serial.available())
  {
    c = Serial.read();
    if (c != '\n')
    {
      // Add to buffer
      serial_buf[sp++] = c; 
    } else {
      // EOL character received, process command
      serial_buf[sp] = '\0';
      process_serial();
      reset_serial_buffer();
    } 
  }
}

void process_serial()
{
  if (strcmp(serial_buf, (char*) F("list_ssid")))
    list_SSID();
  else if (strcmp(serial_buf, (char*) F("set_ssid")))
    set_WiFi(ssid, 1);
  else if (strcmp(serial_buf, (char*) F("set_pass")))
    set_WiFi(pass, 1 + MAX_WIFI_LENGTH);
  else if (strcmp(serial_buf, (char*) F("init_wifi")))
    init_WiFi();
  else if (strcmp(serial_buf, (char*) F("reset")))
    EEPROM_reset();
  else
    Serial.println(F("E0: Unknown command"));
}

void init_WiFi()
{
  if (setup_WiFi()) 
  {
    // Toggle valid WiFi data bit in EEPROM
    EEPROM.write(0, 'W');
    EEPROM.commit();  
      
    // Connect MQTT client
    mqtt_client.setServer(broker, port);
    // Report success to Python
    Serial.println(F("OK"));  
  } else {
    // Report error to Python
    Serial.println(F("E1: Unable to establish WiFi connection"));
  }
}

void list_SSID() 
{
  int numberOfNetworks = WiFi.scanNetworks();
  Serial.print(F("{"));
  for(int i =0; i<numberOfNetworks; i++)
  {
    Serial.print(F("\""));
    Serial.print(WiFi.SSID(i));
    Serial.print(F("\":\""));
    Serial.print(WiFi.RSSI(i));
    Serial.print(F("\""));
    if (i < numberOfNetworks - 1) 
      Serial.print(F(","));
  }
  Serial.println(F("}"));
}

void set_WiFi(char* data, int loc)
{
  char c;
  while (!Serial.available()) 
  { // Wait for SSID data to arrive
  }

  reset_serial_buffer();
  while (Serial.available())
  {
    c = Serial.read();
    if (c != '\n')
    {
      // Add to buffer
      serial_buf[sp++] = c; 
    } else {
      // EOL character received, process command
      write_EEPROM(loc, sp, serial_buf);
      reset_serial_buffer();
      // Report success to Python
      Serial.println(F("OK"));
    } 
  } 
}

void EEPROM_reset(void)
{
  for (int i = 0 ; i < EEPROM_SIZE ; i++) {
    EEPROM.write(i, 0);
  }
  EEPROM.commit();
}

bool check_EEPROM_init(void)
{
  char data[MAX_WIFI_LENGTH];
  char c = EEPROM.read(1);
  if (c == 'W') 
  {
    // Read data from EEPROM
    read_EEPROM(1, data);
    strcpy(data, ssid);
    read_EEPROM(1 + MAX_WIFI_LENGTH, data);
    strcpy(data, pass);
    return true;
  }
  else
    return false;
}

void write_EEPROM(int loc, int len, char* data)
{
  // Valid data key on first bit
  for (int i=0; i<len; i++)
  {
    EEPROM.write(1+loc+i, data[i]);
  }
  EEPROM.write(1+loc+len, '\0');
  EEPROM.commit();
}

void read_EEPROM(int loc, char* data)
{
  int i = 0;
  char c;
  // Valid data in EEPROM, read and return
  while(c != '\0')
  {
    c = EEPROM.read(1+loc+i);
    data[i++] = c;
  }
  data[i] = '\0'; 
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
    Serial.print(F("Attempting MQTT connection..."));
    // Attempt to connect
    if (mqtt_client.connect(node_uuid, MQTT_USER, MQTT_API_KEY)) {
      Serial.println(F("connected"));
    } else {
      Serial.println(F(" try again in 5 seconds"));
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

void mqtt_publish(int id, float value) {
  // Publish float
  // MQTT client connection
  if (!mqtt_client.connected())  // Reconnect if connection is lost
    mqtt_reconnect();

  // Publish value
  char charTopic[TOPIC_LENGTH];
  char charID[MAX_LENGTH_SIGNED_INT];
  char charValue[6];
  strcpy(charTopic, (const char *) F("nodes/"));
  strcat(charTopic, node_uuid);
  strcat(charTopic, (const char *) F("/sensors/"));
  itoa(id, charID, 10);
  strcat(charTopic, charID);
  dtostrf(value, 1, 2, charValue);

  Serial.print(F("MQTT upload on topic: "));
  Serial.print(charTopic);
  Serial.print(F(" => "));
  Serial.println(charValue);
  mqtt_client.publish(charTopic, charValue, true);
}

void mqtt_publish(int id, int value) {
  // Publish int
  // MQTT client connection
  if (!mqtt_client.connected())  // Reconnect if connection is lost
    mqtt_reconnect();
    
  // Publish value
  char charTopic[TOPIC_LENGTH];
  char charID[MAX_LENGTH_SIGNED_INT];
  char charValue[6];
  strcpy(charTopic, (const char *) F("nodes/"));
  strcat(charTopic, node_uuid);
  strcat(charTopic, (const char *) F("/sensors/"));
  itoa(id, charID, 10);
  strcat(charTopic, charID);
  dtostrf(value, 1, 2, charValue);

  Serial.print(F("MQTT upload on topic: "));
  Serial.print(charTopic);
  Serial.print(F(" => "));
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
      {
          np.add_to_buffer(MS_PER_HOUR / delta_t_ms, P_PV, BUF_LENGTH);
          P_PV_value = np.filt_mean(P_PV, BUF_LENGTH, 1);
      }
      last_pulse = millis();
    }
  } 

  // If no pulse within time-out window assume
  // power below minimum power, write 0 to buffer
  if (delta_t_ms > MIN_PV_DT) {
    np.add_to_buffer(0, P_PV, BUF_LENGTH);
    P_PV_value = np.filt_mean(P_PV, BUF_LENGTH, 1);
  }

  // If P_PV changed, publish it to MQTT broker
  if (P_PV_value != P_PV_prev_value) {
    mqtt_publish(P_PV_ID, P_PV_value);
  }
  
  // Store current S0 state for future reference
  S0_prev_state = S0_cur_state;
}
