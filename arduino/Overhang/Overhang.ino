#include <Crc16.h>

// Configuration
#define SERIAL_BUFFER 32
#define CRC_LENGTH 4 // 16 bits, encoded in HEX

// Pins
#define LIGHT_PIN 2
#define STROBE_PIN 3

// Serial buffer
char charSerial[SERIAL_BUFFER] = "";

// CRC16 library
Crc16 crc;
char charCrc[CRC_LENGTH+1] = "0000";
bool boolCrc;

void setup() {
  Serial.begin(4800);
}

void loop() {
  // Receive any inbound messages
  recCrc(true);
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
