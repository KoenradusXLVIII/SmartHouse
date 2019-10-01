// Public libraries
#include <ESP8266WiFi.h>
#include <OneWire.h>

// Private libraries
#include <Json.h>
#include <Numpy.h>
#include <Nebula.h>

// Local includes
#include "config.h"

// Aliases
#define OFF 0
#define ON 1

// WiFi server configuration
#define MAX_LINE_LENGTH 200
char ssid[] = WIFI_SSID;
char pass[] = WIFI_PASSWD;
WiFiServer server(80);

// Blink configuration
const int blinkPin =  LED_BUILTIN;
const long blinkInterval = 1000;              // Blink every second
unsigned long previousBlink = 0;

// JSON Interface
#define VAR_COUNT 3
char charResponse[1 + VAR_COUNT * (1 + VAR_NAME_MAX_LENGTH + 1 + 1 + VAR_VALUE_MAX_LENGTH + 1) - 1 + 1 + 1];
char charCommand[VAR_NAME_MAX_LENGTH + VAR_VALUE_MAX_LENGTH + 1] = "";
const char charInvalid[] PROGMEM = "Invalid parameter";

// Local variable definition
// ! Put the local IO last !
const char var_array[VAR_COUNT][VAR_NAME_MAX_LENGTH] = {"motor_light", "strobe"};
float value_array[VAR_COUNT] = {OFF, OFF};
int sensor_id_array[VAR_COUNT] = {19, 90};
Json json;

// I/O Variables 
#define IO_START 0
int IO_pin_array[VAR_COUNT] = {D0, D1};

// WiFi client configuration
#define UPLOAD_RATE 5
Nebula nebula(NEBULA_API_KEY, UPLOAD_RATE, VAR_COUNT);

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
  for (int i = IO_START; i < VAR_COUNT; i++) {
    pinMode(IO_pin_array[i - IO_START], OUTPUT);
    digitalWrite(IO_pin_array[i - IO_START], !value_array[i]);
  }
}

void loop() {

  // Blink handling
  unsigned long currentBlink = millis();
  if (currentBlink - previousBlink >= blinkInterval) {
    previousBlink = currentBlink;
    digitalWrite(blinkPin, !digitalRead(blinkPin));
  }

  // IO handling
  for (int i = IO_START; i < VAR_COUNT; i++) {
    if (value_array[i] != digitalRead(IO_pin_array[i-IO_START]))
      digitalWrite(IO_pin_array[i-IO_START], value_array[i]); 
  }
    
  // Nebula handling
  nebula.update(sensor_id_array, value_array);

  // JSON server handling
  handle_JSON_server();
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

void parse_command(char * command)
{
  float var_value;

  json.parse_command(command);

  if (strcmp(json.get_var_name(), "all") == 0) {
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
      strcpy(charResponse, charInvalid);
    } else {
      if (json.get_cmd_type() == 'G') {
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
      strcpy(charResponse, json.get_response());
    }
  }
}

int get_id_from_name(char * var_name) {
  for (int i = 0; i < VAR_COUNT; i++ ) {
    if (strcmp(var_array[i], var_name) == 0)
      return i;
  }
  return -1;
}

void return_all() {
  // Initialize variables
  char charValue[VAR_VALUE_MAX_LENGTH];

  strcpy(charResponse, "{\"");
  for (int i = 0; i < VAR_COUNT; i++ ) {
    strcat(charResponse, var_array[i]);
    strcat(charResponse, "\":");
    dtostrf(value_array[i], 3, 2, charValue);
    strcat(charResponse, charValue);
    if (i < (VAR_COUNT - 1))
      strcat(charResponse, ",\"");
  }
  strcat(charResponse, "}");
}
