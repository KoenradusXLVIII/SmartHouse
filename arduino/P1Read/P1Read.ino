#include <AltSoftSerial.h>
// AltSoftSerial always uses these pins:
//
// Board          Transmit  Receive   PWM Unusable
// -----          --------  -------   ------------
// Arduino Uno        9         8         10

// Defines
#define BUFSIZE 75

// Globals
// AltSoftSerial
AltSoftSerial altSerial;
char c;
char buffer[BUFSIZE];
int bufpos = 0;

// P1 telegram
float P_max = 5000.0; // W
float P_min = -2200.0; // W
float P_avg; // W
long E_last = 0; // Wh
long E_cur = 0; // Wh
int E_init = 0;
int E_init_cnt = 10;
unsigned long t_last; // ms
unsigned long t_cur; // ms
unsigned long t_delta; // ms
float t_delta_hour; // h
long cnt_i = 0;
long cnt_d = 0;
long E_import_low; // W
long E_import_high; // W
long E_export_low; // W
long E_export_high; // WdigitalWrite(6, HIGH);

// S0 counter
long E_PV = 0; // Wh
int S0_prev_state = 1;
int S0_pin = 7;

// Water counter
long H2O = 0; // liter
int H2O_prev_state = 0;
int H2O_pin = 6;

void setup() {
  Serial.begin(115200);
  altSerial.begin(115200);
  pinMode(S0_pin,INPUT_PULLUP);
  pinMode(H2O_pin, INPUT);
  //pinMode(6, OUTPUT);
  //digitalWrite(6, LOW);
  t_last = millis();
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

void H2O_read(void) {
  int H2O_cur_state = digitalRead(H2O_pin);

  if(H2O_prev_state == 0)
  {
    if (H2O_cur_state == 1)
    { // Start of pulse detected
      E_PV += 1;
    }
  }

  H2O_prev_state = H2O_cur_state;
}

void process_telegram(void) {
  // Compute current net usage
  E_cur = E_import_low + E_import_high - E_export_low - E_export_high;
  if(E_cur != E_last) {

    // New value received, check validity
    t_cur = millis();
    t_delta = t_cur - t_last; // ms
    t_delta_hour = (float) t_delta/(1000.0*60.0*60.0); // hours

    P_avg = ((float) E_cur - (float) E_last) / t_delta_hour; // W
    if (((P_avg < P_max) && (P_avg > P_min)) || (E_init < E_init_cnt)) { // Sample validated or initializing
      E_last = E_cur;
      t_last = t_cur;
      if ((P_avg < P_max) && (P_avg > P_min) && (E_init != E_init_cnt)) {  // Sample valid, exit initialization
        E_init = E_init_cnt;
        Serial.println("[DEBUG] Initialization complete");
      } else if (E_init != E_init_cnt) {
        E_init += 1;
        Serial.print("[DEBUG] Initialization iteration ");
        Serial.print(E_init);
        Serial.print("\n");
      }
    }
  }
}

void decode_telegram(void) {
  if (altSerial.available()) {
    c = altSerial.read();
    buffer[bufpos] = c;
    bufpos++;

    if(c == '\n') { // End of line detected
      if (sscanf(buffer,"1-0:1.8.1(%ld.%ld" ,&cnt_i, &cnt_d)==2) {
          cnt_i *= 1000; // kWh -> Wh
          cnt_i += cnt_d; // Wh
          E_import_low = cnt_i; // Wh
          //Serial.println(buffer);
      }

      if (sscanf(buffer,"1-0:1.8.2(%ld.%ld" ,&cnt_i, &cnt_d)==2) {
          cnt_i *= 1000; // kWh -> Wh
          cnt_i += cnt_d; // Wh
          E_import_high = cnt_i; // Wh
          //Serial.println(buffer);
      }

      if (sscanf(buffer,"1-0:2.8.1(%ld.%ld" ,&cnt_i, &cnt_d)==2) {
          cnt_i *= 1000; // kWh -> Wh
          cnt_i += cnt_d; // Wh
          E_export_low = cnt_i; // Wh
          //Serial.println(buffer);
      }

      if (sscanf(buffer,"1-0:2.8.2(%ld.%ld" ,&cnt_i, &cnt_d)==2) {
          cnt_i *= 1000; // kWh -> Wh
          cnt_i += cnt_d; // Wh
          E_export_high = cnt_i; // Wh
          //Serial.println(buffer);
      }

      if(buffer[0] == '!') { // End of telegram detected
        // Process telegram
        process_telegram();

        // Report result
        if(E_init == E_init_cnt) {
          Serial.print("E_net: ");
          Serial.println(E_last);
          Serial.print("E_PV: ");
          Serial.println(E_PV);
          Serial.print("H2O: ");
          Serial.println(H2O);
        }
      }

      // Flush buffer
      for (int i=0; i<BUFSIZE; i++)
        buffer[i] = 0;
      bufpos = 0;
    }

    if (bufpos == BUFSIZE) {
      // Flush buffer
      for (int i=0; i<BUFSIZE; i++)
        buffer[i] = 0;
      bufpos = 0;
    }
  }
}

void loop() {
  // Read S0 input
  S0_read();

  // Read serial P1 input
  decode_telegram();
}
