/*
MIT License

Copyright (c) 2018 Joost Verberk

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

#include "Arduino.h"
#include "json.h"

Json::Json()
{
  // Constructor is empty
}

void Json::parse_command(String command)
{
  // Intialise variables
  cmd_type = 'G';     // Default to GET command
  var_name = command;

  for (int i = 0; i < command.length(); i++ ){
    if (command.charAt(i) == '/') { // Command contains '/', so this is a SET command
      cmd_type = 'S';
      var_name = command.substring(0,i);
      var_value = command.substring(i+1,command.length()).toInt();
      break;
    } 
  }
}

char Json::get_cmd_type(void)
{
  return cmd_type;
}

String Json::get_var_name(void)
{
  return var_name;
}

int Json::get_var_value(void)
{
  return var_value;
}

void Json::set_var_value(int set_var_value)
{
  var_value = set_var_value;
}


String Json::get_response(void)
{
  String response = "{" + var_name + ":" + var_value + "}";
  return response;
}
