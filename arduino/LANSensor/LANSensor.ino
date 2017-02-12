/*
Ethernet shield attached to pins 10, 11, 12, 13
*/

#include <SPI.h>
#include <Ethernet.h>
#include <dht.h>

#define DHT21_PIN 2
#define DOOR_CONTACT_PIN 3
#define LIGHT_RELAY_PIN 4
#define BUFFER 64
#define CLOSED 0
#define OPEN 1

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

dht DHT;
float buf_temp[BUFFER];
float buf_humi[BUFFER];
int LightDelay = 30; // seconds

//float temp;
//float humi;

void setup() {
  // Open serial communications and wait for port to open:
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }

  // Initialze inputs
  pinMode(DOOR_CONTACT_PIN,INPUT);
  pinMode(LIGHT_RELAY_PIN,OUTPUT);
  
  // start the Ethernet connection and the server:
  Ethernet.begin(mac, ip);
  Serial.print("Starting ethernet host...");
  server.begin();
  Serial.println("[DONE]");
  Serial.print("LANSensor IP: ");
  Serial.println(Ethernet.localIP());
  
  // Fill buffer with initial data
  Serial.print("Initializing measurement buffer..."); 
  for (int n = 0; n < BUFFER; n++) {
    DHT.read21(DHT21_PIN);
    buf_temp[n] = DHT.temperature;
    buf_humi[n] = DHT.humidity;
  }
  Serial.println("[DONE]");

  // Debugging
  float d1 = 100.0;
  int d2 = 33;
  Serial.print("Division result: ");
  Serial.println(float(d1/d2));
}

void loop() {
  // Initialize variables
    // DHT variables
      float temp;
      float humi;
    // Digital I/O variables
      int cur_door_state = CLOSED;    // Default to closed
      int prev_door_state = CLOSED;   // Default to closed
      unsigned long close_time;
      bool timer_on = false;          // Default timer off
    // Ethernet variables
      String command;
    
  // Get new filtered DHT21 values [0 = temp, 1 = humi]
  temp = read_filtered_DHT(buf_temp,0);
  humi = read_filtered_DHT(buf_humi,1); 

  // Process digital I/0
  cur_door_state = digitalRead(DOOR_CONTACT_PIN);
  if((prev_door_state == OPEN) and (cur_door_state == CLOSED)) {
    // Door was open and is now closed, start countdown
    close_time = millis();
    timer_on = true;
  } else if ((prev_door_state == CLOSED) and (cur_door_state == CLOSED)) {
    // Door was closed and is closed
    if(timer_on) {
      if (millis() - close_time < (LightDelay * 1000)) {
        // Timer has expired, turn light off
        digitalWrite(LIGHT_RELAY_PIN, LOW);
        timer_on = false;
      }
    }
  } else { // cur_door_state == OPEN
    // Door is open, turn light on
    digitalWrite(LIGHT_RELAY_PIN, HIGH);
  }  
  
  // Processe ethernet clients
  EthernetClient client = server.available();
  if (client) {
    String readline;
    String command;
    
    Serial.print("Handling new incoming request... ");
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
          int cnt = 0;
          
          for (int i = 0; i < command.length(); i++ ){
            if (command.charAt(i) == '/') {
              cnt++;
              if (cnt == 1) {
                // SET command received, strip remaining characters
                cmd_type = 'S';
                command.remove(i);
              }
              else if(cnt == 2) {
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
            } else {
              // Unknown variable
              client.println("HTTP/1.1 400 Unkown variable");
              client.println("Connection: close");
            }
          }          

          // If a SET command is received execute
          // the request if the variable is known
          if (cmd_type == 'S'){
            if (command == "LightDelay") {
              if(command.toInt()) {
                LightDelay = command.toInt();
                
                // Inform client
                client.println("HTTP/1.1 200 OK");      
                client.println("Content-Type: text/json");
                client.println("Connection: close");      
                client.println();
                client.print("{\"LightDelay\":");
                client.print(LightDelay);
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
          Serial.println(readline);
          if (readline.startsWith("GET")) {
            // GET command received, stripping...
            command = readline;
            command.remove(5, command.length()-5);  // Strip "GET /"
            command.remove(command.length()-9);      // Strip " HTTP/1.1"
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
  }
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
      Serial.println("[ERROR] Unknown sensor type");
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

/*
void read_DHT() {
  // Read new sensor reading, append to buffer and delete oldest reading
  DHT.read21(DHT21_PIN);
  for (int n = (BUFFER - 1); n > 0; n--) {
    buf_temp[n] = buf_temp[n - 1];
    buf_humi[n] = buf_humi[n - 1];    
  }
  buf_temp[0] = DHT.temperature;
  buf_humi[0] = DHT.humidity;
  
  float tempsum = 0;
  float humisum = 0;
  float tempdiff = 0;
  float humidiff = 0;

  // Compute mean and standard deviation
  for (int n = 0; n < BUFFER; n++) {
    tempsum += buf_temp[n];
    humisum += buf_humi[n];
  }
  float tempmean = float(tempsum / BUFFER);
  float humimean = float(humisum / BUFFER);
  for (int n = 0; n < BUFFER; n++) {
    tempdiff += ((buf_temp[n] - tempmean) * (buf_temp[n] - tempmean));
    humidiff += ((buf_humi[n] - humimean) * (buf_humi[n] - humimean));
  }
  float tempsd = sqrt(tempdiff / (BUFFER - 1));
  float humisd = sqrt(humidiff / (BUFFER - 1));

  // Recompute mean, while excluding samples removed 
  // further then one standard deviation from the mean
  float newtempsum = 0;
  float newtemplen = 0;
  for (int n = 0; n < BUFFER; n++) {
    if((buf_temp[n] <= (tempmean + tempsd)) and (buf_temp[n] >= (tempmean - tempsd))) {
      newtempsum += buf_temp[n];
      newtemplen++;
    }
  }
  temp = newtempsum / newtemplen;
  
  float newhumisum = 0;
  float newhumilen = 0;
  for (int n = 0; n < BUFFER; n++) {
    if((buf_humi[n] <= (humimean + humisd)) and (buf_humi[n] >= (humimean - humisd))) {
        newhumisum += buf_humi[n];
        newhumilen++;
    }
  }
  humi = newhumisum / newhumilen;
}
*/
