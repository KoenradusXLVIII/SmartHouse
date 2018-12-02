#include "Json.h"

#define VAR_COUNT 2

Json json;

int value_array[VAR_COUNT] = {15,80};
String var_array[VAR_COUNT] = {"temp","humi"};

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
  String command;
  String response;

  command = "temp";
  response = parse_command(command);
  Serial.println(response);
  delay(2000);  
  command = "humi/70";
  response = parse_command(command);
  Serial.println(response);  
  delay(2000);
  command = "all";
  response = parse_command(command);
  Serial.println(response);  
  delay(2000);  
  command = "kaas";
  response = parse_command(command);
  Serial.println(response);  
  delay(2000);
}

String parse_command(String command)
{
  int var_value;

  json.parse_command(command);

  if (json.get_var_name() == "all") {
    // All parameters requested
    return return_all();
  } else {
    // Single parameter requested
    // Verify if it is valid
    int id = get_id_from_name(json.get_var_name());
    if (id == -1) {
      // Invalid parameter received
      return F("Invalid parameter");
    } else {
      if (json.get_cmd_type() == 'G'){
        // Retrieve value from array
        var_value = value_array[id];
        // Write to JSON parser
        json.set_var_value(var_value);
      } else { // cmd_type == 'S'
        // Write value to array
        value_array[id] = json.get_var_value();;
      }
      return json.get_response();
    }
  }
}

int get_id_from_name(String var_name){
  for (int i = 0; i < VAR_COUNT; i++ ){
    if(var_array[i] == var_name)
      return i;
  }
  return -1;
}

String return_all() {
  String response = F("{\"");
  for (int i = 0; i < VAR_COUNT; i++ ){
    response += var_array[i];
    response += F("\":");
    response += value_array[i];
    if (i < (VAR_COUNT - 1))
      response += ", \""; 
  }
  response += F("}");
  return response;
}
