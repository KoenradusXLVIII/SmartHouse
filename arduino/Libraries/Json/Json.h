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
#ifndef Json_h
#define Json_h

#include "Arduino.h"

#define VAR_NAME_MAX_LENGTH 16 // 11 characters and '\0'
#define VAR_VALUE_MAX_LENGTH 16 // max 9.999.999 (7 digits and '\0')
#define ALL "all"
#define INVALID "Invalid parameter"

class Json
{
  public:
    Json(int intVarCount);  // Constructor
    void process(char * charJsonInput, char * charJsonOutput, const char charVarNames[][VAR_NAME_MAX_LENGTH], float * floatVarValues);
  private:
    // Functions
    int get_id_from_name(char * charVarName, const char charVarNames[][VAR_NAME_MAX_LENGTH]);
    void parse_all(char * charJsonOutput, const char charVarNames[][VAR_NAME_MAX_LENGTH], float * floatVarValues); 
    void parse_single(char * charJsonOutput, const char charVarNames[][VAR_NAME_MAX_LENGTH], float * floatVarValues, int intVarId);    
    // Variables
    int _intVarCount;
};

#endif
