// Public libraries
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <EEPROM.h>

// Private libraries
#include <Blink.h>
#include <Numpy.h>

// Local includes
#include "config.h"
#include "aliases.h"

// Specific libraries
#include <OneWire.h>

// WiFi client configuration
char ssid[MAX_WIFI_LENGTH];
char pass[MAX_WIFI_LENGTH];
WiFiClient WifiClient;

// Blink configuration
#define BLINK_UNCONFIGURED 5000
#define BLINK_CONFIGURED 1000
Blink blink(LED_BUILTIN); 

// MQTT configuration
#define TOPIC_LENGTH 64
PubSubClient mqtt_client(WifiClient);
char node_uuid[12];
char charTopic[20];
int prev_rssi = 0;
int rssi_buf[BUF_LENGTH];

// Serial configuration
#define SERIAL_SPEED 115200
#define SERIAL_BUF_LENGTH 32
char serial_buf[SERIAL_BUF_LENGTH];
int sp;

// Numpy
Numpy np;

// EEPROM
bool EEPROM_initialized = false;

// Global timing
unsigned long longPrevious = millis();

// ============================= //
// SPECIFIC CONFIGURATION STARTS //
// ============================= //

// DS18B20
#define TEMP_ID 85
OneWire  ds(D2);  // on pin D2
byte addr[8] = {0x28, 0xE0, 0xC4, 0x19, 0x17, 0x13, 0x01, 0x76};
float calibration = 2.0;
float temp_buf[BUF_LENGTH];

// ============================= //
//  SPECIFIC CONFIGURATION ENDS  //
// ============================= //

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
    Serial.print(F("."));
    i++;
  }

  if (WiFi.status() != WL_CONNECTED)
    return false;

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
  Serial.println(F("."));

  // Initialise WiFi
  WiFi.setAutoConnect(0);

  // Extract node UUID
  byte mac[6];
  WiFi.macAddress(mac);
  array_to_string(mac, 6, node_uuid);

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

    // Setup MQTT broker connection
    mqtt_client.setServer(broker, port);
    
  } else {   
    // Node not configured for WiFi
    Serial.println(F("Node not configured"));
    
    // Update blink interval
    blink.set_interval(BLINK_UNCONFIGURED);

    // Initialise serial interface for read
    reset_serial_buffer();

    // ===================== //
    // SPECIFIC SETUP STARTS //
    // ===================== //

    // ===================== //
    //  SPECIFIC SETUP ENDS  //
    // ===================== //
  }
}

void loop() {
  // Blink handling
  blink.update();

  // Listen on serial port
  listen_serial();
    
  if (EEPROM_initialized)
  { // If node is configured...
    // Handle MQTT traffic
    mqtt_client.loop();

    // Report RSSI
    mqtt_rssi();

    // ============================== //
    // SPECIFIC FUNCTION CALLS STARTS //
    // ============================== //
    
    mqtt_temp(); 

    // ============================== //
    //  SPECIFIC FUNCTION CALLS ENDS  //
    // ============================== //
  }
}

// ========================= //
// SPECIFIC FUNCTIONS STARTS //
// ========================= //
    
// Read temperature sensors
void mqtt_temp(void) {
  np.add_to_buffer(DS18B20_read(addr), temp_buf, BUF_LENGTH);
  mqtt_publish(TEMP_ID, np.filt_mean(temp_buf, BUF_LENGTH, 1), 1);  
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

//
// Python Serial communcation functions
//
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
  if (strcmp(serial_buf, (char*) F("list_ssid")) == 0)
    list_SSID();
  else if (strcmp(serial_buf, (char*) F("set_ssid")) == 0)
    set_WiFi(ssid, 1);
  else if (strcmp(serial_buf, (char*) F("set_pass")) == 0)
    set_WiFi(pass, 1 + MAX_WIFI_LENGTH);
  else if (strcmp(serial_buf, (char*) F("init_wifi")) == 0)
    init_WiFi();
  else if (strcmp(serial_buf, (char*) F("reset")) == 0)
    EEPROM_reset();
  else if (strcmp(serial_buf, (char*) F("get_uuid")) == 0)
    Serial.println(node_uuid);
  else if (strcmp(serial_buf, (char*) F("get_ssid")) == 0)
    Serial.println(ssid);
  else if (strcmp(serial_buf, (char*) F("get_wifi_status")) == 0)
    Serial.println(WiFi.status());
  else if (strcmp(serial_buf, (char*) F("get_ip")) == 0)
    Serial.println(WiFi.localIP());
  else
    Serial.println(F("E0: Unknown command"));
}

void reset_serial_buffer(void)
{
  sp = 0;
  for(int i=0; i<SERIAL_BUF_LENGTH; i++)
  { // Initialize serial buffer
    serial_buf[i] = '\0';
  }
}

void init_WiFi()
{
  // Read SSID/pass from EEPROM
  char data[MAX_WIFI_LENGTH];
  read_EEPROM(1, data);
  strcpy(ssid, data);
  read_EEPROM(1 + MAX_WIFI_LENGTH, data);
  strcpy(pass, data);

  // Actively disconnect from any connected WiFi
  WiFi.disconnect();
  delay(100);
  
  if (setup_WiFi()) 
  {
    // Toggle valid WiFi data bit in EEPROM
    EEPROM.write(0, 'W');
    EEPROM.commit();  
      
    // Connect MQTT client
    mqtt_client.setServer(broker, port);
    
    // Update blink interval
    blink.set_interval(BLINK_CONFIGURED);
    
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
  Serial.println(F("OK"));
  char c;
  while (!Serial.available()) 
  { // Wait for SSID data to arrive
  }

  reset_serial_buffer();
  while (Serial.available())
  {
    c = Serial.read();
    // Serial.print(c);
    if (c != '\n')
    {
      // Add to buffer
      serial_buf[sp++] = c; 
    } else {
      // EOL character received, process command
      write_EEPROM(loc, sp, serial_buf);
      // Report success to Python
      Serial.println(serial_buf);
      // Reset serial buffer
      reset_serial_buffer();
    } 
    // Wait for next character
    delay(1);
  } 
}

void EEPROM_reset(void)
{
  for (int i = 0 ; i < EEPROM.length() ; i++) {
    EEPROM.write(i, 0);
  }
  EEPROM.commit();
  EEPROM_initialized = false;

  // Disconnect WiFi
  WiFi.disconnect();

  // Set blink to unconfigured
  blink.set_interval(BLINK_UNCONFIGURED);

  // Report to Python
  Serial.println(F("OK"));
}

//
// EEPROM functions
// 

bool check_EEPROM_init(void)
{
  char data[MAX_WIFI_LENGTH];
  char c = EEPROM.read(0);
  if (c == 'W') 
  {
    // Read data from EEPROM
    read_EEPROM(1, data);
    strcpy(ssid, data);
    read_EEPROM(1 + MAX_WIFI_LENGTH, data);
    strcpy(pass, data);
    return true;
  }
  else
    return false;
}

void write_EEPROM(int loc, int len, char* data)
{
  // Valid data key on first bit
  for (int i=0; i<len; i++)
    EEPROM.write(loc+i, data[i]);
  EEPROM.write(loc+len, '\0');
  EEPROM.commit();
}

void read_EEPROM(int loc, char* data)
{
  int i = 0;
  char c;
  // Valid data in EEPROM, read and return
  while(c != '\0')
  {
    c = EEPROM.read(loc+i);
    data[i++] = c;
  }
  data[i] = '\0'; 
}

//
// WiFi functions
//

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

//
// MQTT functions
//

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

void mqtt_publish(int id, float value, int interval) {
  unsigned long longNow = millis();
  
  if (longNow - longPrevious >= (interval*60000)) {
    // Reset ticker
    longPrevious = longNow;
    
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
}

void mqtt_publish(int id, float value) {
  // Publish float without interval
  mqtt_publish(id, value, 0);
}

void mqtt_publish(int id, int value, int interval) {
  // Publish int with interval
  mqtt_publish(id, (float) value, interval);
}

void mqtt_publish(int id, int value) {
  // Publish int without interval
  mqtt_publish(id, (float) value, 0);
}

void mqtt_rssi(void) {
    int rssi;
    
    np.add_to_buffer((int) WiFi.RSSI(), rssi_buf, BUF_LENGTH);
    rssi = np.filt_mean(rssi_buf, BUF_LENGTH, 1);  
  
    if (rssi != prev_rssi) 
    {
      // Update previous value
      prev_rssi = rssi;
      
      // MQTT client connection
      if (!mqtt_client.connected())  // Reconnect if connection is lost
        mqtt_reconnect();
    
      // Publish value
      char charTopic[TOPIC_LENGTH];
      char charID[MAX_LENGTH_SIGNED_INT];
      char charValue[6];
      strcpy(charTopic, (const char *) F("nodes/"));
      strcat(charTopic, node_uuid);
      strcat(charTopic, (const char *) F("/rssi"));
      dtostrf(rssi, 1, 2, charValue);
    
      Serial.print(F("MQTT upload on topic: "));
      Serial.print(charTopic);
      Serial.print(F(" => "));
      Serial.println(charValue);
      mqtt_client.publish(charTopic, charValue, true);  
    }
}