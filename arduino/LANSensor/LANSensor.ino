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
#define WATER_VALVE_PIN 6
#define WATER_OVERRIDE_PIN 7
#define RAIN_IN_PIN 8
#define RAIN_OUT_PIN 9
#define SHT10_DATA_PIN 14
#define SHT10_CLK_PIN 15
#define LIGHT_SENSOR_PIN 16

// Configuration
#define BUFFER 64
#define RAIN_CALIBRATION 3 // ml/pulse
#define VAR_COUNT 7

// Aliases
#define CLOSED 0
#define OPEN 1
#define MANUAL 0
#define AUTO 1
#define OFF 0
#define ON 1
#define TEMP 0
#define HUMI 1
#define LIGHT 0
#define DARK 1
#define DAY 0
#define NIGHT 1

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

// Public variable array
String var_array[VAR_COUNT] = {"temp", "humi", "rain", "soil_humi", "door_state", "light_state", "light_delay"};
float value_array[VAR_COUNT] = {0, 0, 0, 0, CLOSED, OFF, 30000};

// Define variables
  float buf_temp[BUFFER];
  float buf_humi[BUFFER];
  
  // Digital I/O variables
  int prev_door_state = CLOSED;         // Default to closed
  int light_soft_override_state = AUTO; // Default to AUTO mode 
  unsigned long close_time;
  bool timer_on = false;                // Default timer off
  int water_valve_state = OFF;          // Default to water off
  int water_hard_override_state = AUTO; // Default to AUTO mode  
  int water_soft_override_state = AUTO; // Default to AUTO mode

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
  pinMode(WATER_VALVE_PIN,OUTPUT);
  pinMode(WATER_OVERRIDE_PIN,INPUT_PULLUP);
  pinMode(RAIN_OUT_PIN, OUTPUT);
  pinMode(RAIN_IN_PIN, INPUT_PULLUP);
  pinMode(LIGHT_SENSOR_PIN, INPUT);

  // Initialize output pin values
  digitalWrite(RAIN_OUT_PIN, LOW);  

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
  value_array[get_id_from_name("temp")] = read_filtered_DHT(buf_temp,TEMP);
  value_array[get_id_from_name("humi")] = read_filtered_DHT(buf_humi,HUMI);

  // Door state
  value_array[get_id_from_name("door_state")] = digitalRead(DOOR_CONTACT_PIN);

  // Light
  light_control();
  
  // Water
  water_control();

  // Rain sensor
  rain_sensor();

  // Soil moisture sensor
  value_array[get_id_from_name("soil_humi")] = sht10.readHumidity();
  
  // Processe ethernet clients
  EthernetClient client = server.available();
  if (client) {
    String readline;
    String command;

    //Serial.print("Handling new incoming request... ");
    // an http request ends with a blank line
    boolean currentLineIsBlank = true;
    while (client.connected()) {
      if (client.available()) {
        char c = client.read();
        //Serial.write(c);

        // Store the HTTP request line
        if (readline.length() < 100) {
          readline += c;
        }

        // if you've gotten to the end of the line (received a newline
        // character) and the line is blank, the http request has ended,
        // so you can send a reply
        if (c == '\n' && currentLineIsBlank) {
          // Parse command
          String response;
          response = parse_command(command);

          // Initialise JSON response
          client.println(F("HTTP/1.1 200 OK"));
          client.println(F("Content-Type: text/json"));
          client.println(F("Connection: close"));
          client.println();
          client.println(response);
          break;
        }

        // EOL character received
        if (c == '\n') {
          //Serial.println(readline);
          if (readline.startsWith("GET")) {
            // GET command received, stripping...
            command = readline;
            command.remove(0, 5);  // Strip "GET /"
            command.remove(command.length()-11);      // Strip " HTTP/1.1"
          }
          readline = "";
          currentLineIsBlank = true;

        // Carriage Return received
        } else if (c != '\r') {
          // you've gotten a character on the current line
          currentLineIsBlank = false;
        }
      }
    }
    // give the web browser time to receive the data
    delay(1);
    // close the connection:
    client.stop();
    Serial.println(F("[DONE]"));
  }
}

void rain_sensor(void)
{
  // Read input pin
  int cur_rain_state = digitalRead(RAIN_IN_PIN);
  if ((cur_rain_state == LOW) and (prev_rain_state == HIGH)) {
    // Start of pulse detected
    value_array[get_id_from_name("rain")] += RAIN_CALIBRATION;
  }

  // Store current rain state for future reference
  prev_rain_state = cur_rain_state;  
}

void water_control(void)
{
  int water_hard_override_state = digitalRead(WATER_OVERRIDE_PIN);
  if ((water_hard_override_state == MANUAL) or (water_soft_override_state == MANUAL)) {
    // Manual override on water, set valve to OPEN
    water_valve_state = OPEN;
  } else {
    // Automatic mode, set valve to CLOSED
    water_valve_state = CLOSED;
  }
  digitalWrite(WATER_VALVE_PIN, water_valve_state);
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
      if ((millis() - close_time) > (value_array[get_id_from_name("light_delay")])) {
        // Timer has expired, turn light off
        value_array[get_id_from_name("light_state")] = OFF;
        timer_on = false;
      }
    }
  } else { // cur_door_state == OPEN
    // Door is open, ...
    int light_hard_override_state = digitalRead(LIGHT_OVERRIDE_PIN);
    if (value_array[get_id_from_name("light_state")] == ON)
      light_sensor = DARK;
    if ((light_hard_override_state == AUTO) and (light_soft_override_state == AUTO) and (light_sensor == DARK)) {
      // ... if no overrides present.
      value_array[get_id_from_name("light_state")] = ON;
    } else {
       // ... otherwise turn OFF
      value_array[get_id_from_name("light_state")] = OFF;
    }
  }
  digitalWrite(LIGHT_RELAY_PIN, value_array[get_id_from_name("light_state")]);    
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
      Serial.println(F("[ERROR] Unknown sensor type"));
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

String parse_command(String command)
{
  int var_value;

  json.parse_command(command);

  if (json.get_var_name() == "all") {
    // All parameters requested
    return return_all();
  } else {
    // Single parameter requested
    // Verify if it is valid
    int id = get_id_from_name(json.get_var_name());
    if (id == -1) {
      // Invalid parameter received
      return F("Invalid parameter");
    } else {
      if (json.get_cmd_type() == 'G'){
        // Retrieve value from array
        var_value = value_array[id];
        // Write to JSON parser
        json.set_var_value(var_value);
      } else { // cmd_type == 'S'
        // Write value to array
        value_array[id] = json.get_var_value();;
      }
      return json.get_response();
    }
  }
}

int get_id_from_name(String var_name){
  for (int i = 0; i < VAR_COUNT; i++ ){
    if(var_array[i] == var_name)
      return i;
  }
  return -1;
}

String return_all() {
  String response = F("{\"");
  for (int i = 0; i < VAR_COUNT; i++ ){
    response += var_array[i];
    response += F("\":");
    response += value_array[i];
    if (i < (VAR_COUNT - 1))
      response += ", \""; 
  }
  response += F("}");
  return response;
}
