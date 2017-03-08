/*
Ethernet shield attached to pins 10, 11, 12, 13
*/

#include <SPI.h>
#include <EtherCard.h>

// Enter a MAC address and IP address for your controller below.
// The IP address will be dependent on your local network:
static byte mymac[] = { 0x74,0x69,0x69,0x2D,0x30,0x31 };
static byte myip[] = { 192,168,1,113 };

// Initialize the Ethernet server library
// with the IP address and port you want to use
// (port 80 is default for HTTP):
byte Ethernet::buffer[500];
BufferFiller bfill;

// S0 counter
long E_PV = 0; // Wh
int S0_prev_state = 1;
int S0_pin = 7;

void setup() {
  // Open serial communications and wait for port to open:
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }

  // Setup pins
  pinMode(S0_pin,INPUT_PULLUP);

  // Start the Ethercard connection and the server:
  Serial.print("Starting ethernet host...");
  if (ether.begin(sizeof Ethernet::buffer, mymac) == 0)
    Serial.println("[FAILED]");
  Serial.println("[DONE]");
  ether.staticSetup(myip);
  ether.printIp("Ethercard IP:  ", ether.myip);
}

void S0_read(void) {
  int S0_cur_state = digitalRead(S0_pin);

  if(S0_prev_state == 1)
  {
    if (S0_cur_state == 0)
    { // Start of pulse detected
      E_PV += 1;
    }
  }

  S0_prev_state = S0_cur_state;
}

void loop() {

   // Read S0 input
  S0_read();

  // Processe ethernet clients 
  word len = ether.packetReceive();
  word pos = ether.packetLoop(len);  
  if (pos) {
    String readline;
    String command;
    boolean currentLineIsBlank = true;

    //Serial.print("len: ");
    //Serial.println(len);
    //Serial.print("pos: ");
    //Serial.println(pos);
    
    bfill = ether.tcpOffset();
    char *data = (char *) Ethernet::buffer + pos;

    for(int i = 0; i < len; i++) {
      // Read character from buffer
      char c = data[i];
      
      // Store the HTTP request line
      if (readline.length() < 100) {
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
              Serial.println("Invalid command");
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
            "{\"PV\": $L}"),E_PV);            
          } else if (command == "pv") {
            bfill.emit_p(PSTR(
            "HTTP/1.0 200 OK\r\n"
            "Content-Type: text/json\r\n"
            "Connection: close\r\n"
            "\r\n"
            "{\"PV\": $L}"),E_PV);     
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
