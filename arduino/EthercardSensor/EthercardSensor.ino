/*
Ethernet shield attached to pins 10, 11, 12, 13
*/

#include <SPI.h>
#include <EtherCard.h>

#define BUFFER 5
#define E_PV_RESTORE 457149         // Wh
#define H20_RESTORE 15069           // l
#define MIN_PV_POWER 10             // W
#define MS_PER_HOUR 3600000  
#define SERIAL_SPEED 9600
#define HTTP_MAX_LINE_LENGTH 100

// Enter a MAC address and IP address for your controller below.
// The IP address will be dependent on your local network:
static byte mymac[] = { 0x74,0x69,0x69,0x2D,0x30,0x31 };
static byte myip[] = { 192,168,1,113 };

// Initialize the Ethernet server library
// with the IP address and port you want to use
// (port 80 is default for HTTP):
byte Ethernet::buffer[500];
BufferFiller bfill;

// Energy and power variables
long E_PV = E_PV_RESTORE; // Wh
int P_PV[BUFFER]; // W

// S0 counter
int S0_prev_state = 1;
int S0_pin = 7;
unsigned long delta_t_ms = 0;
unsigned long last_pulse = millis();
bool first_pulse = true;
unsigned long S0_timeout_ms = 3600 / MIN_PV_POWER * 1000;

// Water counter
long H2O = H20_RESTORE; // liter
int H2O_prev_state = 0;
int H2O_pin = 6;

void setup() {
  // Open serial communications and wait for port to open:
  Serial.begin(SERIAL_SPEED);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }

  // Setup pins
  pinMode(S0_pin,INPUT_PULLUP);
  pinMode(H2O_pin,INPUT);

  // Start the Ethercard connection and the server:
  Serial.print("Starting ethernet host...");
  if (ether.begin(sizeof Ethernet::buffer, mymac) == 0)
    Serial.println(F("[FAILED]"));
  Serial.println(F("[DONE]"));
  ether.staticSetup(myip);
  ether.printIp("Ethercard IP:  ", ether.myip);

  // Initialize PV power buffer
  for (int n = 0; n < BUFFER; n++) {
    P_PV[n] = 0;
  }
}

void H2O_read(void) {
  int H2O_cur_state = digitalRead(H2O_pin);

  if(H2O_prev_state == 0)
  {
    if (H2O_cur_state == 1)
    { // Start of pulse detected
      H2O += 1;
    }
  }

  H2O_prev_state = H2O_cur_state;
}

void S0_read(void) {
  // Read input pin
  int S0_cur_state = digitalRead(S0_pin);

  // Compute time difference
  delta_t_ms = millis()-last_pulse; // ms

  if(S0_prev_state == 1)
  {
    if (S0_cur_state == 0)
    { // Start of pulse detected
      E_PV += 1;
      if (delta_t_ms > 0) { // Avoid devide by zero
        P_PV_add_rotate(MS_PER_HOUR / delta_t_ms);
      last_pulse = millis();
    }
  } 

  // If no pulse within time-out window assume
  // power below minimum power, write 0W to buffer
  if (delta_t_ms > S0_timeout_ms)
    P_PV_add_rotate(0);

  // Store current S0 state for future reference
  S0_prev_state = S0_cur_state;
}

void loop() {

   // Read S0 input
  S0_read();

  // Read H2O input
  H2O_read();

  // Processe ethernet clients
  word len = ether.packetReceive();
  word pos = ether.packetLoop(len);
  if (pos) {
    String readline;
    String command;
    boolean currentLineIsBlank = true;

    bfill = ether.tcpOffset();
    char *data = (char *) Ethernet::buffer + pos;

    for(int i = 0; i < len; i++) {
      // Read character from buffer
      char c = data[i];

      // Store the HTTP request line
      if (readline.length() < HTTP_MAX_LINE_LENGTH) {
        readline += c;
      }

      // if you've gotten to the end of the line (received a newline
      // character) and the line is blank, the http request has ended,
      // so you can send a reply
      if (c == '\n' && currentLineIsBlank) {
        bfill = ether.tcpOffset();

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
              bfill.emit_p(PSTR(
              "HTTP/1.0 400 Invalid command\r\n"
              "Connection: close\r\n"));
              ether.httpServerReply(bfill.position());
              break;
            }
          }
        }

        // If a GET command is received execute
        // the request if the variable is known
        if (cmd_type == 'G'){
          if (command == "all") {
            bfill.emit_p(PSTR(
            "HTTP/1.0 200 OK\r\n"
            "Content-Type: text/json\r\n"
            "Connection: close\r\n"
            "\r\n"
            "{\"E_PV\": $L,"
            "\"P_PV\": $D,"
            "\"H2O\": $L}"),E_PV,P_PV_average(),H2O);
          } else if (command == "E_PV") {
            bfill.emit_p(PSTR(
            "HTTP/1.0 200 OK\r\n"
            "Content-Type: text/json\r\n"
            "Connection: close\r\n"
            "\r\n"
            "{\"E_PV\": $L}"),E_PV);
          } else if (command == "P_PV") {
            bfill.emit_p(PSTR(
            "HTTP/1.0 200 OK\r\n"
            "Content-Type: text/json\r\n"
            "Connection: close\r\n"
            "\r\n"
            "{\"P_PV\": $D}"),P_PV_average());
          } else if (command == "H2O") {
            bfill.emit_p(PSTR(
            "HTTP/1.0 200 OK\r\n"
            "Content-Type: text/json\r\n"
            "Connection: close\r\n"
            "\r\n"
            "{\"H2O\": $D}"),H2O);
          } else if (command == "S0") {
            bfill.emit_p(PSTR(
            "HTTP/1.0 200 OK\r\n"
            "Content-Type: text/json\r\n"
            "Connection: close\r\n"
            "\r\n"
            "{\"S0_prev_state\": $D,"
            "\"delta_t_ms\": $L,"
            "\"first_pulse\": $D}"),S0_prev_state,delta_t_ms,first_pulse);
          } else {
            bfill.emit_p(PSTR(
            "HTTP/1.0 400 Unknown variable\r\n"
            "Connection: close\r\n"));
          }
        }

        // HTTP response
        ether.httpServerReply(bfill.position());
      }

      // EOL character received
      if (c == '\n') {
        //Serial.println(readline);
        if (readline.startsWith("GET")) {
          // GET command received, stripping...
          command = readline;
          command.remove(0, 5);  // Strip "GET /"
          command.remove(command.length()-11);      // Strip " HTTP/1.1"
          Serial.print("command: ");
          Serial.println(command);
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
}

// Function to add new value to P_PV buffer and rotate
void P_PV_add_rotate(int P0) {
  for (int n = (BUFFER - 1); n > 0; n--) {
    P_PV[n] = P_PV[n - 1];
  }
  P_PV[0] = P0;
}

// Function to compute average power
int P_PV_average(void) {
  int average = 0;

  for (int n = 0; n < BUFFER; n++) {
    average += P_PV[n];
  }

  return average / BUFFER;
}
