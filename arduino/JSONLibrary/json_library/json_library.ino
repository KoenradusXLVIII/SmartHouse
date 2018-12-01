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
}

String parse_command(String command)
{
  int var_value;

  json.parse_command(command);
  if (json.get_cmd_type() == 'G'){
    // Retrieve value from array
    var_value = value_array[get_id_from_name(json.get_var_name())];
    // Write to JSON parser
    json.set_var_value(var_value);
  } else { // cmd_type == 'S'
    // Write value to array
    value_array[get_id_from_name(json.get_var_name())] = json.get_var_value();;
  }
  return json.get_response();
}

int get_id_from_name(String var_name){
  for (int i = 0; i < VAR_COUNT; i++ ){
    if(var_array[i] == var_name)
      return i;
  }
}
