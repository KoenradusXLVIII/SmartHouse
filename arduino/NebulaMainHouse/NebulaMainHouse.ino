// Public libraries
#include <ESP8266WiFi.h>
#include <OneWire.h>

// Private libraries
#include <Json.h>
#include <Numpy.h>
#include <Nebula.h>
#include <Blink.h>

// Local includes
#include "config.h"
#include "defaults.h"

// WiFi server configuration
#define MAX_LINE_LENGTH 200
char ssid[] = WIFI_SSID;
char pass[] = WIFI_PASSWD;
WiFiServer server(80);

// Blink configuration
Blink blink(LED_BUILTIN, 1000);     // Blink every second            

// JSON Interface
#define VAR_COUNT 5
char charJsonInput[VAR_NAME_MAX_LENGTH + VAR_VALUE_MAX_LENGTH + 1] = "";
char charJsonOutput[3 + VAR_COUNT * (4 + VAR_NAME_MAX_LENGTH + VAR_VALUE_MAX_LENGTH)];
Json json(VAR_COUNT);

// S0 configuration
#define E_PV_RESTORE 1241332                 // Wh
#define H20_RESTORE 28207                    // l
#define MS_PER_HOUR 3600000                  // ms
#define MIN_PV_DT MS_PER_HOUR / 10           // 10W minimum per ms
#define MAX_PV_DT MS_PER_HOUR / 2100         // (2kW + 5% margin = 2.1kW) maximum per ms
#define BUF_LENGTH 5
#define S0 3
float P_PV[BUF_LENGTH]; // W
int S0_prev_state = 1;
unsigned long last_pulse = millis();

// H20 configuration
#define H2O 2
int H2O_prev_state = 0;

// Local variable definition
const char var_array[VAR_COUNT][VAR_NAME_MAX_LENGTH] = {"light", "strobe", "H2O", "E_PV", "P_PV"};
float value_array[VAR_COUNT] = {OFF, OFF, H20_RESTORE, E_PV_RESTORE, 0};

// I/O Variables 
int IO_pin[VAR_COUNT] = {D0, D1, D2, D3, NA};
int IO_pin_dir[VAR_COUNT] = {OUTPUT, OUTPUT, INPUT, INPUT_PULLUP, NA};

// Nebula configuration
#define UPLOAD_RATE 5
Nebula nebula(NEBULA_API_KEY, NEBULA_NODE_UUID, UPLOAD_RATE, VAR_COUNT);
int sensor_id_array[VAR_COUNT] = {};

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
  Serial.print(F("MAC Address: "));
  Serial.println(WiFi.macAddress());  

  // Start the server
  server.begin();

  // Register the Nebula client
  nebula.connect(WiFi.localIP(), WiFi.macAddress());

  // Set I/O
  for (int i = 0; i < VAR_COUNT; i++) {
    if (IO_pin[i] != NA) {
      pinMode(IO_pin[i], IO_pin_dir[i]);
      digitalWrite(IO_pin[i], !value_array[i]);
    }
  }
}

void loop() {

  // Blink handling
  blink.update();
    
  // Nebula handling
  //nebula.update(sensor_id_array, value_array);

  // JSON server handling ...
  handle_JSON_server();
  // ... and associated local output handling
  for (int i = 0; i < VAR_COUNT; i++) {
    if (IO_pin_dir[i] == OUTPUT) {
      if (value_array[i] != digitalRead(IO_pin[i]))
        digitalWrite(IO_pin[i], value_array[i]); 
    }
  }

  // Local input handling
  H2O_read();
  S0_read(); 
}

void H2O_read(void) {
  int H2O_cur_state = digitalRead(IO_pin[H2O]);

  // Upward flink
  if(H2O_prev_state == 0)
  {
    if (H2O_cur_state == 1)
    { // Start of pulse detected
      value_array[H2O] += 1;
    }
  }

  H2O_prev_state = H2O_cur_state;
}

void S0_read(void) {
  // Read input pin
  int S0_cur_state = digitalRead(IO_pin[S0]);

  // Compute time difference
  unsigned long delta_t_ms = millis()-last_pulse; // ms

  // Downward flank
  if(S0_prev_state == 1)
  {
    if (S0_cur_state == 0)
    { // Start of pulse detected
      value_array[S0] += 1;
      if (delta_t_ms > MAX_PV_DT) // Avoid invalid power calculation
        value_array[S0] = filtered_buffer(P_PV, BUF_LENGTH, MS_PER_HOUR / delta_t_ms);
      last_pulse = millis();
    }
  } 

  // If no pulse within time-out window assume
  // power below minimum power, write 0W to buffer
  if (delta_t_ms > MIN_PV_DT)
    value_array[S0] = filtered_buffer(P_PV, BUF_LENGTH, 0);

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
          if (strlen(charJsonInput)) {
            json.process(charJsonInput, charJsonOutput, var_array, value_array);
          }

          // Initialise JSON response
          client.println(F("HTTP/1.1 200 OK"));
          client.println(F("Content-Type: text/json"));
          client.println(F("Connection: close"));
          client.println();
          client.println(charJsonOutput);
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
              strncpy(charJsonInput, &charReadLine[5], strlen(charReadLine) - 16);
              charJsonInput[strlen(charReadLine) - 16] = '\0';
            } else {
              charJsonInput[0] = '\0';
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
