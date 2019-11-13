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
#ifndef Numpy_h
#define Numpy_h

#include "Arduino.h"

class Numpy
{
  public:
    Numpy(); // Constructor
    void add_to_buffer(float new_data, float *buf_data, int buf_length);
    void add_to_buffer(int new_data, int *buf_data, int buf_length);
    float filt_mean(float *buf_data, int buf_length, int nr_std);
    int filt_mean(int *buf_data, int buf_length, int nr_std);
    float mean(float *buf_data, int buf_length);
    int mean(int *buf_data, int buf_length);
    float std(float *buf_data, int buf_length);
    int std(int *buf_data, int buf_length);
  private:
    // Empty
};

#endif
