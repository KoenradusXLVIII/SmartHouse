#include "Json.h"

#define VAR_COUNT 11

Json json;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
}

void loop() {

 
  char var_array[VAR_COUNT][VAR_NAME_MAX_LENGTH] =
   {"temp", "humi", "rain", "soil_humi", "door_state", 
    "light_state", "light_delay", "valve_state", 
    "alarm_mode", "light_mode", "water_mode"};

  if(strcmp(var_array[6],"light") == 0){
    Serial.println("Match!");
  }

  delay(10000);
}
