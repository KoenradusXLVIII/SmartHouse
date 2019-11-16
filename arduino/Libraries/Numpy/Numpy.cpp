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
#include "Numpy.h"

Numpy::Numpy()
{
  // Constructor is empty
}

void Numpy::add_to_buffer(float new_data, float *buf_data, int buf_length)
{
  // Rotate buffer and add new value, instance for floats
  for (int n = (buf_length - 1); n > 0; n--) {
    buf_data[n] = buf_data[n - 1];
  }

  // Append new data
  buf_data[0] = new_data;
}

void Numpy::add_to_buffer(int new_data, int *buf_data, int buf_length)
{
  // Rotate buffer and add new value, instance for ints
  for (int n = (buf_length - 1); n > 0; n--) {
    buf_data[n] = buf_data[n - 1];
  }

  // Append new data
  buf_data[0] = new_data;
}

float Numpy::filt_mean(float *buf_data, int buf_length, int nr_std)
{
  // Compute filtered mean, which excludes samples
  // removed further then *nr_std* standard deviations
  // from the mean, instance for floats
  
  // Compute mean and standard deviation
  Numpy np;
  float mean = np.mean(buf_data, buf_length);
  float std = np.std(buf_data, buf_length);
  
  // Recompute mean, while excluding samples removed
  // further then one standard deviation from the mean
  float sum = 0.0;
  int len = 0;
  for (int n = 0; n < buf_length; n++) {
    if((buf_data[n] <= (mean + nr_std*std)) and (buf_data[n] >= (mean - nr_std*std))) {
      sum += buf_data[n];
      len++;
    }
  }
  
  return float(sum/len);  
}

int Numpy::filt_mean(int *buf_data, int buf_length, int nr_std)
{
  // Compute filtered mean, which excludes samples
  // removed further then *nr_std* standard deviations
  // from the mean, instance for ints

  // Compute mean and standard deviation
  Numpy np;
  int mean = np.mean(buf_data, buf_length);
  int std = np.std(buf_data, buf_length);

  // Recompute mean, while excluding samples removed
  // further then one standard deviation from the mean
  int sum = 0;
  int len = 0;
  for (int n = 0; n < buf_length; n++) {
    if((buf_data[n] <= (mean + nr_std*std)) and (buf_data[n] >= (mean - nr_std*std))) {
      sum += buf_data[n];
      len++;
    }
  }

  return int(sum/len);
}

float Numpy::mean(float *buf_data, int buf_length)
{
  // Compute mean for floats
  float sum = 0.0;
  for (int n = 0; n < buf_length; n++) {
    sum += buf_data[n];
  }
  return float(sum / buf_length);    
}

int Numpy::mean(int *buf_data, int buf_length)
{
  // Compute mean for ints
  int sum = 0;
  for (int n = 0; n < buf_length; n++) {
    sum += buf_data[n];
  }
  return int(sum / buf_length);
}

float Numpy::std(float *buf_data, int buf_length)
{
  // Instance for floats
  // Compute mean
  Numpy np;
  float mean = np.mean(buf_data, buf_length);
  
  // Compute standard deviation
  float diff = 0.0;
  for (int n = 0; n < buf_length; n++) {
    diff += ((buf_data[n] - mean) * (buf_data[n] - mean));
  }
  return float(sqrt(diff / (buf_length - 1)));    
}

int Numpy::std(int *buf_data, int buf_length)
{
  // Instance for floats
  // Compute mean
  Numpy np;
  int mean = np.mean(buf_data, buf_length);

  // Compute standard deviation
  int diff = 0;
  for (int n = 0; n < buf_length; n++) {
    diff += ((buf_data[n] - mean) * (buf_data[n] - mean));
  }
  return int(sqrt(diff / (buf_length - 1)));
}

