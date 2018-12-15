#include <SPI.h>
#include <Ethernet.h>
#include <dht.h>
#include <SHT1x.h>
#include "Json.h"

// Pins [Pins 10 through 13 in use by Ethernet shield]
#define DHT21_PIN 2
#define DOOR_CONTACT_PIN 3
#define LIGHT_RELAY_PIN 4
#define LIGHT_OVERRIDE_PIN 5
#define VALVE_PIN 6
#define WATER_OVERRIDE_PIN 7
#define RAIN_IN_PIN 8
#define RAIN_OUT_PIN 9
#define SHT10_DATA_PIN 14
#define SHT10_CLK_PIN 15
#define LIGHT_SENSOR_PIN 16
#define CHRISTMAS_PIN 17

// Configuration
#define BUFFER 64
#define RAIN_CALIBRATION 3 // ml/pulse

// Defines
#define VAR_COUNT 13
#define MAX_LINE_LENGTH 100

// Aliases
#define CLOSED 0
#define OPEN 1
#define MANUAL 0
#define AUTO 1
#define OFF 0
#define ON 1
#define LIGHT 0
#define DARK 1
#define DAY 0
#define NIGHT 1

// Variable order
#define TEMP 0
#define HUMI 1
#define RAIN 2
#define SOIL_HUMI 3
#define DOOR_STATE 4
#define LIGHT_STATE 5
#define LIGHT_DELAY 6
#define VALVE_STATE 7
#define ALARM_MODE 8
#define LIGHT_MODE 9
#define WATER_MODE 10
#define MOTOR_LIGHT 11
#define DAY_NIGHT 12

// Enter a MAC address and IP address for your controller below.
// The IP address will be dependent on your local network:
byte mac[] = {
  0x90, 0xA2, 0xDA, 0x0E, 0xC5, 0x67
};
IPAddress ip(192, 168, 1, 112);

// Initialize the Ethernet server library
// with the IP address and port you want to use
// (port 80 is default for HTTP):
EthernetServer server(80);
// '{"VAR_NAME":VAR_VALUE,"VAR_NAME":VAR_VALUE,...,"VAR_NAME":VAR_VALUE}\0'
char charResponse[1+VAR_COUNT*(1+VAR_NAME_MAX_LENGTH+1+1+VAR_VALUE_MAX_LENGTH+1)-1+1+1];
 
// Initialize SHT10
// VCC - Brown - Red
// GND - Black - Blue/Black
// DAT - Yellow - Red/Yellow
// CLK - Blue - Blue
SHT1x sht10(SHT10_DATA_PIN, SHT10_CLK_PIN);

// DHT sensor
dht DHT;

// JSON library
Json json;

// Define variables
  const char var_array[VAR_COUNT][VAR_NAME_MAX_LENGTH] =
   {"temp", "humi", "rain", "soil_humi", "door_state", 
    "light_state", "light_delay", "valve_state", 
    "alarm_mode", "light_mode", "water_mode",
    "motor_light", "day_night"};
  float value_array[VAR_COUNT] = {0, 0, 0, 0, CLOSED, OFF, 30000, CLOSED, ON, AUTO, AUTO, OFF, DAY};
  const char charInvalid[] PROGMEM = "Invalid parameter";

  // DHT21 value buffer
  float buf_temp[BUFFER];
  float buf_humi[BUFFER];
  
  // Digital I/O variables
  int prev_door_state = CLOSED;         // Default to closed
  int prev_day_night_state = DAY;       // Default to day

  // Timers
  bool timer_on = false;                // Default timer off
  unsigned long close_time;
  
  // Rain sensor
  int prev_rain_state = HIGH;

void setup() {
  // Open serial communications and wait for port to open:
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }

  // Initialze pins
  pinMode(DOOR_CONTACT_PIN,INPUT);
  pinMode(LIGHT_RELAY_PIN,OUTPUT);
  pinMode(LIGHT_OVERRIDE_PIN,INPUT_PULLUP);
  pinMode(VALVE_PIN,OUTPUT);
  pinMode(WATER_OVERRIDE_PIN,INPUT_PULLUP);
  pinMode(RAIN_OUT_PIN, OUTPUT);
  pinMode(RAIN_IN_PIN, INPUT_PULLUP);
  pinMode(LIGHT_SENSOR_PIN, INPUT);
  pinMode(CHRISTMAS_PIN, OUTPUT);

  // Initialize output pin values
  digitalWrite(RAIN_OUT_PIN, LOW);  
  digitalWrite(LIGHT_RELAY_PIN, LOW);  
  digitalWrite(VALVE_PIN, LOW);
  digitalWrite(CHRISTMAS_PIN, LOW);  

  // start the Ethernet connection and the server:
  Ethernet.begin(mac, ip);
  Serial.print(F("Starting ethernet host..."));
  server.begin();
  Serial.println(F("[DONE]"));
  Serial.print(F("LANSensor IP: "));
  Serial.println(Ethernet.localIP());

  // Fill buffer with initial data
  Serial.print(F("Initializing measurement buffer..."));
  for (int n = 0; n < BUFFER; n++) {
    DHT.read21(DHT21_PIN);
    buf_temp[n] = DHT.temperature;
    buf_humi[n] = DHT.humidity;
  }
  Serial.println(F("[DONE]"));
}

void loop() {
  // Get new filtered DHT21 values
  value_array[TEMP] = read_filtered_DHT(buf_temp,TEMP);
  value_array[HUMI] = read_filtered_DHT(buf_humi,HUMI);

  // Door state
  value_array[DOOR_STATE] = digitalRead(DOOR_CONTACT_PIN);

  // Light
  light_control();
  
  // Water
  water_control();

  // Rain sensor
  rain_sensor();

  // Christmas lights
  if((value_array[DAY_NIGHT] == NIGHT) && (prev_day_night_state == DAY))
    digitalWrite(CHRISTMAS_PIN, HIGH);
  else if ((value_array[DAY_NIGHT] == DAY) && (prev_day_night_state == NIGHT))
    digitalWrite(CHRISTMAS_PIN, LOW);    
  prev_day_night_state = value_array[DAY_NIGHT];

  // Soil moisture sensor
  value_array[SOIL_HUMI] = sht10.readHumidity();
  
  // Processe ethernet clients
  EthernetClient client = server.available();
  if (client) {
    char charReadLine[MAX_LINE_LENGTH];
    char charCommand[VAR_NAME_MAX_LENGTH+VAR_VALUE_MAX_LENGTH+1];
    boolean currentLineIsBlank = true;
    int i = 0;
    char c;
    
    while (client.connected()) {
      if (client.available()) {
        // Store the HTTP request line
        c = client.read();
        if (i < MAX_LINE_LENGTH) {
          charReadLine[i] = c;
          charReadLine[i+1] = '\0';
        }
        i++;
                
        // if you've gotten to the end of the line (received a newline
        // character) and the line is blank, the http request has ended,
        // so you can send a reply
        if (c == '\n' && currentLineIsBlank) {
          // Parse command
          //Serial.println(charCommand);
          parse_command(charCommand);
          
          // Initialise JSON response
          client.println(F("HTTP/1.1 200 OK"));
          client.println(F("Content-Type: text/json"));
          client.println(F("Connection: close"));
          client.println();
          client.println(charResponse);
          break;
        }

        if (c == '\n') {
          // EOL character received
          if ((charReadLine[0] == 'G') && (charReadLine[1] == 'E') && (charReadLine[2] == 'T')) {
            // GET command received, stripping... 
            // From the front: "GET /" - 5 characters
            // From the back: " HTTP/1.1" - 9 charachters
            strncpy(charCommand,&charReadLine[5],strlen(charReadLine)-16);
            charCommand[strlen(charReadLine)-16] = '\0';
          }
          // Erase line and reset character pointer
          charReadLine[0] = '\0';
          i = 0;
          currentLineIsBlank = true;
        } else if (c != '\r') {
          currentLineIsBlank = false;
          // Character received on this line      
        }
      }
    }
    // give the web browser time to receive the data
    delay(1);
    // close the connection:
    client.stop();
  }

  // Process serial clients
  {
    // TODO
  }
}

void rain_sensor(void)
{
  // Read input pin
  int cur_rain_state = digitalRead(RAIN_IN_PIN);
  if ((cur_rain_state == LOW) and (prev_rain_state == HIGH)) {
    // Start of pulse detected
    value_array[RAIN] += RAIN_CALIBRATION;
  }

  // Store current rain state for future reference
  prev_rain_state = cur_rain_state;  
}

void water_control(void)
{
  int water_hard_override_state = digitalRead(WATER_OVERRIDE_PIN);
  if ((water_hard_override_state == MANUAL) or (value_array[WATER_MODE] == MANUAL)) {
    // Manual override on water, set valve to OPEN
    value_array[VALVE_STATE] = OPEN;
  } else {
    // Automatic mode, set valve to CLOSED
    value_array[VALVE_STATE] = CLOSED;
  }
  digitalWrite(VALVE_PIN, value_array[VALVE_STATE]);
}

void light_control(void)
{
  int cur_door_state = digitalRead(DOOR_CONTACT_PIN);
  int light_sensor = digitalRead(LIGHT_SENSOR_PIN);
  
  if((prev_door_state == OPEN) and (cur_door_state == CLOSED)) {
    // Door was open and is now closed, start countdown
    close_time = millis();
    timer_on = true;
  } else if ((prev_door_state == CLOSED) and (cur_door_state == CLOSED)) {
    // Door was closed and is closed
    if(timer_on) {
      if ((millis() - close_time) > (value_array[LIGHT_DELAY])) {
        // Timer has expired, turn light off
        value_array[LIGHT_STATE] = OFF;
        timer_on = false;
      }
    }
  } else { // cur_door_state == OPEN
    // Door is open, ...
    int light_hard_override_state = digitalRead(LIGHT_OVERRIDE_PIN);
    if (value_array[LIGHT_STATE] == ON)
      light_sensor = DARK;
    if ((light_hard_override_state == AUTO) and (value_array[LIGHT_MODE] == AUTO) and (light_sensor == DARK)) {
      // ... if no overrides present.
      value_array[LIGHT_STATE] = ON;
    } else {
       // ... otherwise turn OFF
      value_array[LIGHT_STATE] = OFF;
    }
  }
  digitalWrite(LIGHT_RELAY_PIN, value_array[LIGHT_STATE]);    
  prev_door_state = cur_door_state;
}

float read_filtered_DHT(float *buf_data, int sensor) {
  // Read new sensor data
  DHT.read21(DHT21_PIN);
  // Shift buffer
  for (int n = (BUFFER - 1); n > 0; n--) {
    buf_data[n] = buf_data[n - 1];
  }
  // Append new data
  switch(sensor) {
    case 0:
      buf_data[0] = DHT.temperature;
      break;
    case 1:
      buf_data[0] = DHT.humidity;
      break;
    default:
      //Serial.println(F("[ERROR] Unknown sensor type"));
      return 0.0;
  }

  // Declare variables
  float sum = 0.0;
  float diff = 0.0;

  // Compute mean
  for (int n = 0; n < BUFFER; n++) {
    sum += buf_data[n];
  }
  float mean = float(sum / BUFFER);

  // Compute standard deviation
  for (int n = 0; n < BUFFER; n++) {
    diff += ((buf_data[n] - mean) * (buf_data[n] - mean));
  }
  float sd = sqrt(diff / (BUFFER - 1));

  // Recompute mean, while excluding samples removed
  // further then one standard deviation from the mean
  sum = 0.0;
  int len = 0;
  for (int n = 0; n < BUFFER; n++) {
    if((buf_data[n] <= (mean + sd)) and (buf_data[n] >= (mean - sd))) {
      sum += buf_data[n];
      len++;
    }
  }
  return float(sum / len);
}

void parse_command(char * command)
{
  float var_value;

  json.parse_command(command);

  if (strcmp(json.get_var_name(),"all")==0) {
    // All parameters requested
    return_all();
  } else {
    // Single parameter requested
    // Verify if it is valid
    int id = get_id_from_name(json.get_var_name());
    //Serial.print("GET: ");
    //Serial.println(json.get_var_name());     
    if (id == -1) {
      // Invalid parameter received
      strcpy(charResponse,charInvalid);
    } else {
      if (json.get_cmd_type()== 'G'){
        // Retrieve value from array
        //Serial.print("GET: ");
        //Serial.println(id); 
        var_value = value_array[id];
        // Write to JSON parser
        json.set_var_value(var_value);
      } else { // cmd_type == 'S'
        // Write value to array
        value_array[id] = json.get_var_value();;
      }
      strcpy(charResponse,json.get_response());
    }
  }
}

int get_id_from_name(char * var_name){
  for (int i = 0; i < VAR_COUNT; i++ ){
    if(strcmp(var_array[i],var_name) == 0)
      return i;
  }
  return -1;
}

void return_all() {
  // Initialize variables
  char charValue[VAR_VALUE_MAX_LENGTH];
  
  strcpy(charResponse, "{\"");
  for (int i = 0; i < VAR_COUNT; i++ ){
    strcat(charResponse, var_array[i]);
    strcat(charResponse, "\":");
    dtostrf(value_array[i], 3, 2, charValue);
    strcat(charResponse, charValue);
    if (i < (VAR_COUNT - 1))
      strcat(charResponse, ",\""); 
  }
  strcat(charResponse,"}");
}
