#include <SPI.h>
#include <Ethernet.h>
#include <dht.h>
#include <SHT1x.h>

#define DEBUG

// Pins [Pins 10 through 13 in use by Ethernet shield]
#define DHT21_PIN 2
#define DOOR_CONTACT_PIN 3
#define LIGHT_RELAY_PIN 4
#define LIGHT_OVERRIDE_PIN 5
#define WATER_VALVE_PIN 6
#define WATER_OVERRIDE_PIN 7
#define RAIN_IN_PIN 8
#define RAIN_OUT_PIN 9
#define SHT10_DATA_PIN A0
#define SHT10_CLK_PIN A1
#define LIGHT_SENSOR_PIN A2

// Configuration
#define BUFFER 64
#define RAIN_CALIBRATION 3 // ml/pulse

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

// Define variables
  float buf_temp[BUFFER];
  float buf_humi[BUFFER];
  // Digital I/O variables
  int prev_door_state = CLOSED;         // Default to closed
  int light_state = OFF;                // Default to light off
  int light_soft_override_state = AUTO; // Default to AUTO mode 
  unsigned long close_time;
  bool timer_on = false;                // Default timer off
  int water_valve_state = OFF;          // Default to water off
  int water_hard_override_state = AUTO; // Default to AUTO mode  
  int water_soft_override_state = AUTO; // Default to AUTO mode

  // Light sensor
  int light_delay = 30000;          // 30000ms = 30s default

  // Rain sensor
  int prev_rain_state = HIGH;
  unsigned long rain_meter = 0; // in ml

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

  float soil_humi = sht10.readHumidity();
  Serial.println(soil_humi);
}

void loop() {
  // Initialize variables
    // DHT variables
      float temp;
      float humi;
    // Ethernet variables
      String command;

  // Get new filtered DHT21 values
  temp = read_filtered_DHT(buf_temp,TEMP);
  humi = read_filtered_DHT(buf_humi,HUMI);

  // Light
  light_control();
  
  // Water
  water_control();

  // Rain sensor
  rain_sensor();

  // Soil moisture sensor
  float soil_humi = sht10.readHumidity();
  Serial.println(soil_humi);
  
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
          // Parsing command
          char cmd_type = 'G';  // Default to GET command
          String cmd_value;
          int cnt = 0;

          for (int i = 0; i < command.length(); i++ ){
            if (command.charAt(i) == '/') {
              cnt++;
              if (cnt == 1) {
                // SET command received, strip remaining characters
                cmd_type = 'S';
                cmd_value = command;
                cmd_value.remove(0,i+1);
                command.remove(i);
              }
              else if(cnt == 2) {
                Serial.println(F("Invalid command"));
                // Invalid command received
                client.println(F("HTTP/1.1 400 Invalid command"));
                client.println(F("Connection: close"));
                break;
              }
            }
          }

          // If a GET command is received execute
          // the request if the variable is known
          if (cmd_type == 'G'){
            client.println(F("HTTP/1.1 200 OK"));
            client.println(F("Content-Type: text/json"));
            client.println(F("Connection: close"));
            client.println();
            if (command == "all") {
              client.print(F("{\"Temperature\":"));
              client.print(temp);
              client.print(F(", \"Humidity\":"));
              client.print(humi);
              client.print(F(", \"Rain\":"));
              client.print(rain_meter);  
              rain_meter = 0; // Rain meter read, so reset
              client.print(F(", \"Soil Humidity\":"));
              client.print(soil_humi);              
              client.print(F(", \"Door state\":"));
              client.print(prev_door_state);
              client.print(F(", \"Light state\":"));
              client.print(light_state);
              client.print(F(", \"Light delay\":"));
              client.print(light_delay);
              client.println(F("}"));
            } else if (command == "door_state") {
              client.print(F("{\"Door state\":"));
              client.print(prev_door_state);
              client.println(F("}"));
            } else if (command == "temp") {
              client.print(F("{\"Temperature\":"));
              client.print(temp);
              client.println(F("}"));
            } else if (command == "humi") {
              client.print(F("{\"Humidity\":"));
              client.print(humi);
              client.println(F("}"));
            } else if (command == "rain") {
              client.print(F("{\"Rain\":"));
              client.print(rain_meter);
              client.println(F("}"));
              rain_meter = 0; // Rain meter read, so reset       
            } else if (command == "soil_humi") {
              client.print(F("{\"Soil Humidity\":"));
              client.print(soil_humi);
              client.println(F("}"));         
            } else if (command == "light_delay") {
              client.print(F("{\"Light delay\":"));
              client.print(light_delay);
              client.println(F("}"));
            } else if (command == "light_state") {
              client.print(F("{\"Light state\":"));
              client.print(light_state);
              client.println(F("}"));
            } else {
              // Unknown variable
              client.println(F("Unkown variable"));
            }
          }

          // If a SET command is received execute
          // the request if the variable is known
          if (cmd_type == 'S'){
            client.println(F("HTTP/1.1 200 OK"));
            client.println(F("Content-Type: text/json"));
            client.println(F("Connection: close"));
            client.println();
            if (command == "light_delay") {
              if(cmd_value.toInt()) {
                light_delay = cmd_value.toInt();
              } else {
                // Invalid SET parameter received
                client.println(F("Invalid parameter"));
                client.println();
              }

              // Inform client
              client.print(F("{\"Light delay\":"));
              client.print(light_delay);
              client.println(F("}"));
            } else if (command == "light_mode") {
              if(cmd_value == "auto") {
                light_soft_override_state = AUTO;
              } else if (cmd_value == "manual") {
                light_soft_override_state = MANUAL;
              } else {
                // Invalid SET parameter received
                client.println(F("Invalid parameter"));
                client.println();
              }
              
              // Inform client
              client.print(F("{\"Light mode\":"));
              client.print(light_soft_override_state);
              client.println(F("}"));
            } else if (command == "water_mode") {
              if(cmd_value == "auto") {
                water_soft_override_state = AUTO;
              } else if (cmd_value == "manual") {
                water_soft_override_state = MANUAL;
              } else {
                // Invalid SET parameter received
                client.println(F("Invalid parameter"));
                client.println();
              }
              
              // Inform client
              client.print(F("{\"Water mode\":"));
              client.print(water_soft_override_state);
              client.println(F("}"));
            } else {
              // Invalid SET parameter received
              client.println(F("Invalid parameter"));
              client.println();
            }
          }
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
    rain_meter += RAIN_CALIBRATION;
    #ifdef DEBUG
      Serial.print("Rain: ");
      Serial.print(rain_meter);
      Serial.println(" ml");
    #endif
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
      if ((millis() - close_time) > (light_delay)) {
        // Timer has expired, turn light off
        light_state = OFF;
        timer_on = false;
      }
    }
  } else { // cur_door_state == OPEN
    // Door is open, ...
    int light_hard_override_state = digitalRead(LIGHT_OVERRIDE_PIN);
    if (light_state == ON)
      light_sensor = DARK;
    if ((light_hard_override_state == AUTO) and (light_soft_override_state == AUTO) and (light_sensor == DARK)) {
      // ... if no overrides present.
      light_state = ON;
    } else {
       // ... otherwise turn OFF
      light_state = OFF;
    }
  }
  digitalWrite(LIGHT_RELAY_PIN, light_state);    
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
