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
#include "Json.h"

Json::Json()
{
  // Constructor is empty
}

void Json::parse_command(char * charCommand)
{
  // Intialise variables
  int intValue;  
  charCmdType = 'G';     // Default to GET command
  strcpy(charName, charCommand);

  for (int i = 0; i < strlen(charCommand); i++ ){
    if (charCommand[i] == '/') { // Command contains '/', so this is a SET command
      charCmdType = 'S';
      charCommand[i] = ' ';
      sscanf(charCommand,"%s %d", charName, &intValue);
      floatValue = (float)intValue;
      dtostrf(floatValue, 3, 2, charValue);
      break;
    } 
  }
}

char Json::get_cmd_type(void)
{
  return charCmdType;
}

char * Json::get_var_name(void)
{
  return charName;
}

float Json::get_var_value(void)
{
  return floatValue;
}

void Json::set_var_value(float floatSetValue)
{
  floatValue = floatSetValue;
  dtostrf(floatValue, 3, 2, charValue);
}

char * Json::get_response(void)
{ 
  strcpy(charResponse, "{\"");
  strcat(charResponse, charName);
  strcat(charResponse, "\":");
  strcat(charResponse, charValue);
  strcat(charResponse, "}");
  return charResponse;
}
