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

// Constructor
Json::Json(int intVarCount)
{  
  _intVarCount = intVarCount;
}

//
// Public functions
//

void Json::process(char * charJsonInput, char * charJsonOutput, const char charVarNames[][VAR_NAME_MAX_LENGTH], float * floatVarValues)
{
  // Intialise variables 
  char charCmdType;
  char charVarName[VAR_NAME_MAX_LENGTH];
  int floatVarValue; 
  int intVarId;
  
  // Default to GET command
  charCmdType = 'G';
  strcpy(charVarName, charJsonInput);

  // Extract command type, variable name and value
  for (int i = 0; i < strlen(charJsonInput); i++ ){
    if (charJsonInput[i] == '/') { // Command contains '/', so this is a SET command
      charCmdType = 'S';
      charJsonInput[i] = ' ';
      sscanf(charJsonInput,"%s %f", charVarName, &floatVarValue);
      break;
    } 
  }
  
  // Parse command
  if (strcmp(charVarName, ALL) == 0) {
      // All parameters requested
      parse_all(charJsonOutput, charVarNames, floatVarValues);
  } else {
      // Single parameter requested
      intVarId = get_id_from_name(charVarName, charVarNames);
      if (intVarId >= 0) {
          if (charCmdType == 'S') {
              // Write value to array
              floatVarValues[intVarId] = (float) intVarValue;
          } 
          // Write array value to output buffer
          parse_single(charJsonOutput, charVarNames, floatVarValues, intVarId);
      } else {
          // Invalid parameter requested
          strcpy(charJsonOutput, INVALID);
      }
  }  
}

//
// Private functions
//

int Json::get_id_from_name(char * charVarName, const char charVarNames[][VAR_NAME_MAX_LENGTH])
{
  for (int i = 0; i < _intVarCount; i++ ) {
    if (strcmp(charVarNames[i], charVarName) == 0)
      return i;
  }
  return -1;       
}

void Json::parse_all(char * charJsonOutput, const char charVarNames[][VAR_NAME_MAX_LENGTH], float * floatVarValues)
{
  char charVarValue[VAR_NAME_MAX_LENGTH];
  
  strcpy(charJsonOutput, "{\"");
  for (int i = 0; i < _intVarCount; i++ ) {
    strcat(charJsonOutput, charVarNames[i]);
    strcat(charJsonOutput, "\":");
    dtostrf(floatVarValues[i], 3, 2, charVarValue);
    strcat(charJsonOutput, charVarValue);
    if (i < (_intVarCount - 1))
      strcat(charJsonOutput, ",\"");
  }
  strcat(charJsonOutput, "}");    
}

void Json::parse_single(char * charJsonOutput, const char charVarNames[][VAR_NAME_MAX_LENGTH], float * floatVarValues, int intVarId)
{ 
  char charVarValue[VAR_NAME_MAX_LENGTH];
  
  strcpy(charJsonOutput, "{\"");
  strcat(charJsonOutput, charVarNames[intVarId]);
  strcat(charJsonOutput, "\":");
  dtostrf(floatVarValues[intVarId], 3, 2, charVarValue);
  strcat(charJsonOutput, charVarValue);
  strcat(charJsonOutput, "}");
}

