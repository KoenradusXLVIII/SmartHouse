/*
MIT License

Copyright (c) 2019 Joost Verberk

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
#ifndef Nebula_h
#define Nebula_h

#include "Arduino.h"
#include <ESP8266WiFi.h>

#define HOST "http://www.joostverberk.nl"
#define PORT 80

class Nebula
{
  public:
    Nebula(char * APIKey, unsigned long uploadInterval, int nrVariables); // Constructor
    void update(int * sensor_id_array, float * value_array);
    void upload(int * sensor_id_array, float * value_array);

  private:
    void content_length(void)
    unsigned long _previousUpload = 0;
    unsigned long _uploadInterval = 0;
    char _APIKey[36] = "";
    int _nrVariables = 0;

};

#endif
