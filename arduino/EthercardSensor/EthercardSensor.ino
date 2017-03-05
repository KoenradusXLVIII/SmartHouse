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
              //client.println("HTTP/1.1 400 Invalid command");
              //client.println("Connection: close");
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
  /*
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
                Serial.println("Invalid command");
                // Invalid command received
                client.println("HTTP/1.1 400 Invalid command");
                client.println("Connection: close");
                break;
              }
            }
          }

          // If a GET command is received execute
          // the request if the variable is known
          if (cmd_type == 'G'){
            if (command == "all") {
              client.println("HTTP/1.1 200 OK");
              client.println("Content-Type: text/json");
              client.println("Connection: close");
              client.println();
              client.print("{\"Temperature\":");
              client.print(temp);
              client.print(", \"Humidity\":");
              client.print(humi);
              client.print(", \"Door state\":");
              client.print(cur_door_state);
              client.print(", \"Light state\":");
              client.print(light_state);
              client.print(", \"Light delay\":");
              client.print(light_delay);
              client.println("}");
            } else if (command == "door_state") {
              client.println("HTTP/1.1 200 OK");
              client.println("Content-Type: text/json");
              client.println("Connection: close");
              client.println();
              client.print("{\"Door state\":");
              client.print(cur_door_state);
              client.println("}");
            } else if (command == "temp") {
              client.println("HTTP/1.1 200 OK");
              client.println("Content-Type: text/json");
              client.println("Connection: close");
              client.println();
              client.print("{\"Temperature\":");
              client.print(temp);
              client.println("}");
            } else if (command == "humi") {
              client.println("HTTP/1.1 200 OK");
              client.println("Content-Type: text/json");
              client.println("Connection: close");
              client.println();
              client.print("{\"Humidity\":");
              client.print(humi);
              client.println("}");
            } else if (command == "light_delay") {
              client.println("HTTP/1.1 200 OK");
              client.println("Content-Type: text/json");
              client.println("Connection: close");
              client.println();
              client.print("{\"Light delay\":");
              client.print(light_delay);
              client.println("}");
            } else if (command == "light_state") {
              client.println("HTTP/1.1 200 OK");
              client.println("Content-Type: text/json");
              client.println("Connection: close");
              client.println();
              client.print("{\"Light state\":");
              client.print(light_state);
              client.println("}");
            } else {
              // Unknown variable
              client.println("HTTP/1.1 400 Unkown variable");
              client.println("Connection: close");
            }
          }

          // If a SET command is received execute
          // the request if the variable is known
          if (cmd_type == 'S'){
            if (command == "light_delay") {
              if(cmd_value.toInt()) {
                light_delay = cmd_value.toInt();

                // Inform client
                client.println("HTTP/1.1 200 OK");
                client.println("Content-Type: text/json");
                client.println("Connection: close");
                client.println();
                client.print("{\"Light delay\":");
                client.print(light_delay);
                client.println("}");
              } else {
                // Invalid SET parameter received
                client.println("HTTP/1.1 400 Invalid parameter");
                client.println("Connection: close");
              }
            } else if (command == "light_state") {
              if(cmd_value.toInt()) {
                if(cmd_value) {
                  // Turn light on
                  digitalWrite(LIGHT_RELAY_PIN, HIGH);
                  light_state = HIGH;
                } else {
                  // Turn light off
                  digitalWrite(LIGHT_RELAY_PIN, LOW);
                  light_state = LOW;
                }

                // Inform client
                client.println("HTTP/1.1 200 OK");
                client.println("Content-Type: text/json");
                client.println("Connection: close");
                client.println();
                client.print("{\"Light state\":");
                client.print(light_state);
                client.println("}");
              } else {
                // Invalid SET parameter received
                client.println("HTTP/1.1 400 Invalid parameter");
                client.println("Connection: close");
              }
            } else {
              // Unknown variable
              client.println("HTTP/1.1 400 Unkown variable");
              client.println("Connection: close");
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
    Serial.println("[DONE]");
  }*/
}
