// Private libraries
#include <Json.h>

// Local includes
#include "config.h"

// Debug
#define DEBUG 1

// Aliases
#define OFF 0
#define ON 1

// WiFi server configuration
#define MAX_LINE_LENGTH 200
char ssid[] = WIFI_SSID;
char pass[] = WIFI_PASSWD;
WiFiServer server(80);

// WiFi client configuration
const char* host = "http://www.joostverberk.nl";
const uint16_t port = 80;
const long nebulaInterval = 5*60*1000;                      // Update Nebula every 5 minutes          
unsigned long previousNebula = 0;

// Blink configuration
const int blinkPin =  LED_BUILTIN; 
const long blinkInterval = 1000;                            // Blink every second         
unsigned long previousBlink = 0;     
int blinkState = LOW;  

// JSON Interface
#define VAR_COUNT 4
#define SPRINKLER_BACK 0
#define SPRINKLER_FRONT 1
#define RELAY_3 2
#define RELAY_4 3
char charResponse[1 + VAR_COUNT * (1 + VAR_NAME_MAX_LENGTH + 1 + 1 + VAR_VALUE_MAX_LENGTH + 1) - 1 + 1 + 1];
char charCommand[VAR_NAME_MAX_LENGTH + VAR_VALUE_MAX_LENGTH + 1] = "";
const char charInvalid[] PROGMEM = "Invalid parameter";
const char var_array[VAR_COUNT][VAR_NAME_MAX_LENGTH] = {"sprinkler_front", "sprinkler_back", "relay_3", "relay_4"};
float value_array[VAR_COUNT] = {ON, OFF, ON, OFF};
int sensor_id_array[VAR_COUNT] = {87, 86, 88, 89};
Json json;

// I/O Variables
#define SPRINKLER_BACK_PIN D0
#define SPRINKLER_FRONT_PIN D1
#define RELAY_3_PIN D2
#define RELAY_4_PIN D3
int prev_sprinkler_front_state = value_array[SPRINKLER_FRONT];          
int prev_sprinkler_back_state = value_array[SPRINKLER_BACK];          
int prev_relay_3_state = value_array[RELAY_3];                   
int prev_relay_4_state = value_array[RELAY_4];                 

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

  // Initialze pins
  pinMode(blinkPin, OUTPUT);
  pinMode(SPRINKLER_BACK_PIN, OUTPUT);
  pinMode(SPRINKLER_FRONT_PIN, OUTPUT);
  pinMode(RELAY_3_PIN, OUTPUT);
  pinMode(RELAY_4_PIN, OUTPUT);

    // Initialize output pin values
  digitalWrite(SPRINKLER_BACK_PIN, !value_array[SPRINKLER_BACK]);  
  digitalWrite(SPRINKLER_FRONT_PIN, !value_array[SPRINKLER_FRONT]);  
  digitalWrite(RELAY_3_PIN, !value_array[RELAY_3]);
  digitalWrite(RELAY_4_PIN, !value_array[RELAY_4]);  
}

void loop() {
  // Blink handling
  unsigned long currentBlink = millis();
  if (currentBlink - previousBlink >= blinkInterval) {
    previousBlink = currentBlink;
    // if the LED is off turn it on and vice-versa:
    if (blinkState == LOW) {
      blinkState = HIGH;
    } else {
      blinkState = LOW;
    }
    digitalWrite(blinkPin, blinkState);
  }

  // IO handling
  if (value_array[SPRINKLER_BACK] != prev_sprinkler_back_state)
    digitalWrite(SPRINKLER_BACK_PIN, !value_array[SPRINKLER_BACK]);
  prev_sprinkler_back_state = value_array[SPRINKLER_BACK];
  if (value_array[SPRINKLER_FRONT] != prev_sprinkler_front_state)
    digitalWrite(SPRINKLER_FRONT_PIN, !value_array[SPRINKLER_FRONT]);
  prev_sprinkler_front_state = value_array[SPRINKLER_FRONT];
  if (value_array[RELAY_3] != prev_relay_3_state)
    digitalWrite(RELAY_3_PIN, !value_array[RELAY_3]);
  prev_relay_3_state = value_array[RELAY_3];
  if (value_array[RELAY_4] != prev_relay_4_state)
    digitalWrite(RELAY_4_PIN, !value_array[RELAY_4]);
  prev_relay_4_state = value_array[RELAY_4];
  
  // Nebula handling
  unsigned long currentNebula = millis();
  if (currentNebula - previousNebula >= nebulaInterval) {
    previousNebula = currentNebula;
    handle_Nebula();
  }
  
  // JSON server handling
  handle_JSON_server();
}

void handle_Nebula() {  
  // Define variables
  WiFiClient client;
  
  // Compute content length
  int content_length = 2; // {\n
  content_length += 11;   // "api_key":"
  content_length += sizeof(NEBULA_API_KEY);
  content_length += 4;    // ",\r\n
  content_length += 9;    // "values":
  content_length += 3;    // [\r\n
  content_length += 13;   // {"sensor_id":
  content_length += 2;    // xx
  content_length += 9;    // ,"value":
  content_length += 4;    // x.xx
  content_length += 1;    // }
  content_length += 3;    // ,\r\n
  content_length += 13;   // {"sensor_id":
  content_length += 2;    // xx
  content_length += 9;    // ,"value":
  content_length += 4;    // x.xx
  content_length += 1;    // }
  content_length += 3;    // ,\r\n
  content_length += 13;   // {"sensor_id":
  content_length += 2;    // xx
  content_length += 9;    // ,"value":
  content_length += 4;    // x.xx
  content_length += 1;    // }
  content_length += 3;    // ,\r\n
  content_length += 13;   // {"sensor_id":
  content_length += 2;    // xx
  content_length += 9;    // ,"value":
  content_length += 4;    // x.xx
  content_length += 3;    // }\r\n
  content_length += 3;    // ]\r\n
  content_length += 3;    // }\r\n
  content_length += 2;    // \r\n

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
  client.print(F("\"values\":"));
  client.println(F("["));
  client.print(F("{\"sensor_id\":"));
  client.print(sensor_id_array[SPRINKLER_BACK]);
  client.print(F(",\"value\":"));
  client.print(value_array[SPRINKLER_BACK]);
  client.print(F("}"));
  client.println(F(","));
  client.print(F("{\"sensor_id\":"));
  client.print(sensor_id_array[SPRINKLER_FRONT]);
  client.print(F(",\"value\":"));
  client.print(value_array[SPRINKLER_FRONT]);
  client.print(F("}"));
  client.println(F(","));
  client.print(F("{\"sensor_id\":"));
  client.print(sensor_id_array[RELAY_3]);
  client.print(F(",\"value\":"));
  client.print(value_array[RELAY_3]);
  client.print(F("}"));
  client.println(F(","));
  client.print(F("{\"sensor_id\":"));
  client.print(sensor_id_array[RELAY_4]);
  client.print(F(",\"value\":"));
  client.print(value_array[RELAY_4]);
  client.println(F("}"));
  client.println(F("]"));
  client.println(F("}"));
  client.println(F(""));

  if (DEBUG) {
    Serial.println(F("{"));
    Serial.print(F("\"api_key\":\""));
    Serial.print(NEBULA_API_KEY);
    Serial.println(F("\","));
    Serial.print(F("\"values\":"));
    Serial.println(F("["));
    Serial.print(F("{\"sensor_id\":"));
    Serial.print(sensor_id_array[SPRINKLER_BACK]);
    Serial.print(F(",\"value\":"));
    Serial.print(value_array[SPRINKLER_BACK]);
    Serial.print(F("}"));
    Serial.println(F(","));
    Serial.print(F("{\"sensor_id\":"));
    Serial.print(sensor_id_array[SPRINKLER_FRONT]);
    Serial.print(F(",\"value\":"));
    Serial.print(value_array[SPRINKLER_FRONT]);
    Serial.print(F("}"));
    Serial.println(F(","));
    Serial.print(F("{\"sensor_id\":"));
    Serial.print(sensor_id_array[RELAY_3]);
    Serial.print(F(",\"value\":"));
    Serial.print(value_array[RELAY_3]);
    Serial.print(F("}"));
    Serial.println(F(","));
    Serial.print(F("{\"sensor_id\":"));
    Serial.print(sensor_id_array[RELAY_4]);
    Serial.print(F(",\"value\":"));
    Serial.print(value_array[RELAY_4]);
    Serial.println(F("}"));
    Serial.println(F("]"));
    Serial.println(F("}"));
    Serial.println(F(""));

    // wait for data to be available
    unsigned long timeout = millis();
    while (client.available() == 0) {
      if (millis() - timeout > 5000) {
        Serial.println(">>> Client Timeout !");
        client.stop();
        delay(60000);
        return;
      }
    }

    // Read all the lines of the reply from server and print them to Serial
    Serial.println("receiving from remote server");
    // not testing 'client.connected()' since we do not need to send data here
    while (client.available()) {
      char ch = static_cast<char>(client.read());
      Serial.print(ch);
    }
  }
  
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
            //client.print("End of HTTP request, processing charCommand: ");
            //client.println(charCommand);
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
              //client.print(charReadLine);
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

  if (strcmp(json.get_var_name(),"all")==0) {
    // All parameters requested
    return_all();
  } else {
    // Single parameter requested
    // Verify if it is valid
    int id = get_id_from_name(json.get_var_name());
    //client.print("GET: ");
    //client.println(json.get_var_name());     
    if (id == -1) {
      // Invalid parameter received
      strcpy(charResponse,charInvalid);
    } else {
      if (json.get_cmd_type()== 'G'){
        // Retrieve value from array
        //client.print("GET: ");
        //client.println(id); 
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
