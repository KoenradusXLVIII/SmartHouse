#include <Crc16.h>
#include "Json.h"

// Aliases
#define OFF 0
#define ON 1

// Variable order
#define MOTOR_LIGHT 0
#define STROBE 1

// Configuration
#define SERIAL_BUFFER 32
#define CRC_LENGTH 4 // 16 bits, encoded in HEX
#define VAR_COUNT 2

// Pins
#define MOTOR_LIGHT_PIN 2
#define STROBE_PIN 3

// Serial buffer
char charSerial[SERIAL_BUFFER] = "";

// CRC16 library
Crc16 crc;
char charCrc[CRC_LENGTH+1] = "0000";
bool boolCrc;

// JSON library
Json json;

// Define variables
const char var_array[VAR_COUNT][VAR_NAME_MAX_LENGTH] =
 {"motor_light", "strobe"};
float value_array[VAR_COUNT] = {OFF, OFF};

int prev_motor_light_state = OFF;     // Default to off

void setup() {
  Serial.begin(4800);

  // Set pin modes
  pinMode(MOTOR_LIGHT_PIN, OUTPUT);
  pinMode(STROBE_PIN, OUTPUT);

  // Initialize pins
  digitalWrite(MOTOR_LIGHT_PIN, LOW);
  digitalWrite(STROBE_PIN, LOW);
}

void loop() {
  // Receive any inbound messages
  recCrc(true);

  // Motor light
  if((value_array[MOTOR_LIGHT] == OFF) && (prev_motor_light_state == ON))
    digitalWrite(MOTOR_LIGHT_PIN, LOW);
  else if ((value_array[MOTOR_LIGHT] == ON) && (prev_motor_light_state == OFF))
    digitalWrite(MOTOR_LIGHT_PIN, HIGH);
  prev_motor_light_state = value_array[MOTOR_LIGHT]; 
}

bool recCrc(bool boolAck) {
  crc.clearCrc();
  boolCrc = false;
  int i = 0;
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '!') {
      charSerial[i] = '\0';
      boolCrc = true;
      i = 0;
      c = Serial.read();
    }
    if (!boolCrc) {
      charSerial[i++] = c;   
      crc.updateCrc(c);
    } else {
      charCrc[i++] = c;  
    }
    delay(10);   
  }  

  // Process inbound message
  if (strlen(charSerial)) {         // New message detected
    if (boolAck) {                  // Acknowledgement required
      if (checkCrc()) {             // Check CRC
        sendCrc("OK", false);       // Cyclic redundancy check OK, send without expecting acknowledgement
        procMsg();                  // Process the message
        charSerial[0] = '\0';       // Reset serial buffer
        return true;                 
      } else { 
        sendCrc("NOK", false);      // Cyclic redundancy check NOK, send without expecting acknowledgement
        charSerial[0] = '\0';
        return false;
      }
    } else {                        // No acknowledgement required
      return checkCrc();            // Verify CRC
    }   
  }
}

void procMsg(void) {
  json.parse_command(charSerial);
  int id = get_id_from_name(json.get_var_name());
  if (id != 1) {
    value_array[id] = json.get_var_value();  
  }
}

int get_id_from_name(char * var_name){
  for (int i = 0; i < VAR_COUNT; i++ ){
    if(strcmp(var_array[i],var_name) == 0)
      return i;
  }
  return -1;
}

bool checkCrc() {
  unsigned short recCrc = 0;
  for (int i=0; i < CRC_LENGTH; i++) {
    int digit = (charCrc[i] >= 'A') ? charCrc[i] - 'A' + 10 : charCrc[i] - '0';
    recCrc = recCrc + (digit << (4 * (CRC_LENGTH-1-i)));
  } 
  return (recCrc == crc.getCrc());
}

void sendCrc(char * msg, bool boolAck) {
  unsigned short value = crc.XModemCrc(msg,0,strlen(msg));

  // Send message with CRC
  Serial.print(msg);
  Serial.print('!');
  Serial.print(value, HEX);

  // Wait for acknowledgement?
  if (boolAck) {
    while (!Serial.available()) {
    }                                 // Wait for acknowledgement  
    
    if (!recCrc(false))               // Do not re-acknowledge acknowledgement
      delay(1);                       // TODO: Replace with resend
  }
}
