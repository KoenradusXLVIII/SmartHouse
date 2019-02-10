#include <Crc16.h>

// Configuration
#define SERIAL_BUFFER 32
#define CRC_LENGTH 4 // 16 bits, encoded in HEX

// Serial buffer
char charSerial[SERIAL_BUFFER] = "";
char charSerial1[SERIAL_BUFFER] = "";

// CRC16 library
Crc16 crc;
char charCrc[CRC_LENGTH+1] = "0000";
bool boolCrc;

void setup() {
  Serial.begin(9600);
  Serial1.begin(4800);
}

void loop() {
  // Transmit any outbound messages
  if (Serial.available()) {
    int i = 0;                      // Read message from terminal
    while (Serial.available()) {
      charSerial[i++] = Serial.read();
      delay(10);
    }
    charSerial[i] = '\0';           // Terminate message
    sendCrc(charSerial, true);      // Send with CRC
  }
}

bool recCrc(bool boolAck) {
  crc.clearCrc();                   // Reset CRC
  boolCrc = false;
  int i = 0;
  while (Serial1.available()) {     // Read from serial interface
    char c = Serial1.read();
    if (c == '!') {                 // Start of CRC detected
      charSerial[i] = '\0';
      boolCrc = true;
      i = 0;
      c = Serial1.read();
    }
    if (!boolCrc) {
      charSerial[i++] = c;   
      crc.updateCrc(c);             // Update CRC
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

  // Debug
  Serial.print("Message: ");
  Serial.print(charSerial);

  // Send message with CRC
  Serial1.print(msg);
  Serial1.print('!');
  Serial1.print(value, HEX);

  // Wait for acknowledgement?
  if (boolAck) {
    while (!Serial1.available()) {
    }                                 // Wait for acknowledgement  
    
    if (recCrc(false))                // Do not re-acknowledge acknowledgement
      Serial.println(" [OK]");
    else
      Serial.println(" [NOK]");
  }
}
