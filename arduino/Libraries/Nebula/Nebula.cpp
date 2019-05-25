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

#include "Arduino.h"
#include "Nebula.h"

Nebula::Nebula(char * APIKey, unsigned long uploadInterval, int nrVariables) // Constructor
{
  strcpy(_APIKey, APIKey);
  _APIKey[36] = '\0';
  _uploadInterval = uploadInterval*60*1000;
  _nrVariables = nrVariables;
}

//
// Public functions
//

bool Nebula::update(int * sensor_id_array, float * value_array) 
{
  unsigned long now = millis();
  if (now - _previousUpload >= _uploadInterval) {
    _previousUpload = now;
    upload(sensor_id_array, value_array);
    return true;
  }    
  return false;
}

//
// Private functions
//

void Nebula::upload(int * sensor_id_array, float * value_array)
{
    // Instantiate WiFi client
    WiFiClient client;
    client.connect(HOST, PORT);

    // Send POST message
    // Send message header
    client.println(F("POST /api/graph/post.php HTTP/1.1"));
    client.println(F("Host: joostverberk.nl"));
    client.println(F("Content-Type: application/x-www-form-urlencoded"));
    client.println(F("User-Agent: Wemos/1.0"));
    client.println(F("Connection: close"));
    client.print(F("Content-Length: "));
    client.println(content_length());
    client.println(F(""));

    // Send message body
    client.println(F("{"));
    client.print(F("\"api_key\":\""));
    client.print(_APIKey);
    client.println(F("\","));
    client.println(F("\"values\":["));
    for (int i = 0; i < _nrVariables; i++) {
        client.print(F("{\"sensor_id\":"));
        client.print(sensor_id_array[i]);
        client.print(F(",\"value\":"));
        client.print(value_array[i]);        
        if (i < _nrVariables - 1) {
            client.println(F("},"));
        } else {
            client.println(F("}"));           
        }
    }
    client.println(F("]"));
    client.println(F("}"));
    client.println(F(""));
    
    // Send POST message
    // Send message header
    Serial.println(F("POST /api/graph/post.php HTTP/1.1"));
    Serial.println(F("Host: joostverberk.nl"));
    Serial.println(F("Content-Type: application/x-www-form-urlencoded"));
    Serial.println(F("User-Agent: Wemos/1.0"));
    Serial.println(F("Connection: close"));
    Serial.print(F("Content-Length: "));
    Serial.println(content_length());
    Serial.println(F(""));

    // Send message body
    Serial.println(F("{"));
    Serial.print(F("\"api_key\":\""));
    Serial.print(_APIKey);
    Serial.println(F("\","));
    Serial.println(F("\"values\":["));
    for (int i = 0; i < _nrVariables; i++) {
        Serial.print(F("{\"sensor_id\":"));
        Serial.print(sensor_id_array[i]);
        Serial.print(F(",\"value\":"));
        Serial.print(value_array[i]);        
        if (i < _nrVariables - 1) {
            Serial.println(F("},"));
        } else {
            Serial.println(F("}"));           
        }
    }
    Serial.println(F("]"));
    Serial.println(F("}"));
    Serial.println(F(""));    

    // Close connection
    client.stop();
}

int Nebula::content_length(void)
{
    int content_length = 73; // API key and empty values array []
    for (int i = 0; i < _nrVariables; i++) {
        content_length += 32;
    }
    content_length -= 1; // Compensate for last value not having ,
    return content_length;
}


