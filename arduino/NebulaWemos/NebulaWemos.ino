// Public libraries
#include <ESP8266WiFi.h>
#include <OneWire.h>

// Private libraries
#include <Json.h>
#include <Numpy.h>

// Local includes
#include "config.h"

// Aliases
#define OFF 0
#define ON 1

// WiFi server configuration
#define MAX_LINE_LENGTH 200
IPAddress ip(192, 168, 1, 120);
IPAddress gateway(192, 168, 1, 1);
IPAddress subnet(255, 255, 255, 0);
IPAddress dns(8, 8 , 8, 8);
char ssid[] = WIFI_SSID;
char pass[] = WIFI_PASSWD;
WiFiServer server(80);

// WiFi client configuration
const char* host = "http://www.joostverberk.nl";
const uint16_t port = 80;
const long nebulaInterval = 1*60*1000;                      // Update Nebula every 5 minutes          
unsigned long previousNebula = 0;

// Blink configuration
const int blinkPin =  LED_BUILTIN; 
const long blinkInterval = 1000;                            // Blink every second         
unsigned long previousBlink = 0;     
int blinkState = LOW;  

// JSON Interface
#define VAR_COUNT 1
#define TEMP 0
char charResponse[1 + VAR_COUNT * (1 + VAR_NAME_MAX_LENGTH + 1 + 1 + VAR_VALUE_MAX_LENGTH + 1) - 1 + 1 + 1];
char charCommand[VAR_NAME_MAX_LENGTH + VAR_VALUE_MAX_LENGTH + 1] = "";
const char charInvalid[] PROGMEM = "Invalid parameter";
const char var_array[VAR_COUNT][VAR_NAME_MAX_LENGTH] = {"temp"};
float value_array[VAR_COUNT] = {5.0};
int sensor_id_array[VAR_COUNT] = {85};
Json json;

// DS18B20
#define BUF_LENGTH 32
OneWire  ds(D2);  // on pin D2
byte addr[8] = {0x28, 0xE0, 0xC4, 0x19, 0x17, 0x13, 0x01, 0x76};
float calibration = 2.0;
float buf_temp[BUF_LENGTH];

// Numpy
Numpy np;

void setup() {
  Serial.begin(9600);

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

  // Start the server
  server.begin();

  // Set I/O
  pinMode(blinkPin, OUTPUT);
}

void loop() {
  // DS18B20 handling
  value_array[TEMP] = read_filtered_DS18B20(buf_temp, BUF_LENGTH, addr);

  // Nebula handling
  unsigned long currentNebula = millis();
  if (currentNebula - previousNebula >= nebulaInterval) {
    previousNebula = currentNebula;
    handle_Nebula();
  }

  // Blink handling
  unsigned long currentBlink = millis();
  if (currentBlink - previousBlink >= blinkInterval) {
    // if the LED is off turn it on and vice-versa:
    if (blinkState == LOW) {
      blinkState = HIGH;
    } else {
      blinkState = LOW;
    }
    
    digitalWrite(blinkPin, blinkState);
  }
  
  // JSON server handling
  handle_JSON_server();
}

void handle_Nebula() {
  Serial.println("Nebula upload");
  
  // Define variables
  WiFiClient client;
  
  // Compute content length
  int content_length = 2; // {\n
  content_length += 11;   // "api_key":"
  content_length += sizeof(NEBULA_API_KEY);
  content_length += 3;    // ",\n
  content_length += 23;   // "values":[{"sensor_id":
  content_length += 2;    // xx
  content_length += 9;    // ,"value":
  content_length += 5;    // xx.xx
  content_length += 3;    // }]\n
  content_length += 3;    // }\n

  // Connect to Nebula
  client.connect(host, port);

  // Send POST message
  // Send message header
  client.println(F("POST /api/graph/post.php HTTP/1.1"));
  client.println(F("Host: joostverberk.nl"));
  client.println(F("Content-Type: application/x-www-form-urlencoded"));
  client.println(F("User-Agent: Arduino/1.0"));
  client.println(F("Connection: close"));
  // Send computed content-length
  client.print(F("Content-Length: "));
  client.println(content_length);
  client.println(F(""));

  // Send message body
  client.println(F("{"));
  client.print(F("\"api_key\":\""));
  client.print(NEBULA_API_KEY);
  client.println(F("\","));
  client.print(F("\"values\":[{\"sensor_id\":"));
  client.print(sensor_id_array[TEMP]);
  client.print(F(",\"value\":"));
  client.print(value_array[TEMP]);
  client.println(F("}]"));
  client.println(F("}"));
  client.println(F(""));

  // Close connection to Nebula
  client.stop();
}

void handle_JSON_server(void) {
  // Check if a client has connected
  WiFiClient client = server.available();

  if (client) {
    char charReadLine[MAX_LINE_LENGTH];
    boolean currentLineIsBlank = true;
    int i = 0;
    char c;

    while (client.connected()) {
      if (client.available()) {
        // Store the HTTP request line
        c = client.read();
        if (i < MAX_LINE_LENGTH) {
          charReadLine[i] = c;
          charReadLine[i + 1] = '\0';
        }
        i++;

        // if you've gotten to the end of the line (received a newline
        // character) and the line is blank, the http request has ended,
        // so you can send a reply
        if (c == '\n' && currentLineIsBlank) {
          // Parse command
          if (strlen(charCommand)) {
            //Serial.print("End of HTTP request, processing charCommand: ");
            //Serial.println(charCommand);
            parse_command(charCommand);
          }

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
            if ((charReadLine[13] != 'i') && (charReadLine[13] != 'c') && (charReadLine[13] != 'o')) {
              // GET command received, stripping...
              // From the front: "GET /" - 5 characters
              // From the back: " HTTP/1.1" - 9 charachters
              //Serial.print(charReadLine);
              strncpy(charCommand, &charReadLine[5], strlen(charReadLine) - 16);
              charCommand[strlen(charReadLine) - 16] = '\0';
            } else {
              charCommand[0] = '\0';
            }
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
