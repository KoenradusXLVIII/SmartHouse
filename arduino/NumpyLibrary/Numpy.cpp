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

float Numpy::filt_mean(float *buf_data, int buf_length, int nr_std)
{
  // Compute filtered mean, which excludes samples
  // removed further then *nr_std* standard deviations
  // from the mean  
  
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

float Numpy::mean(float *buf_data, int buf_length)
{
  // Compute mean 
  float sum = 0.0;
  for (int n = 0; n < buf_length; n++) {
    sum += buf_data[n];
  }
  return float(sum / buf_length);    
}

float Numpy::std(float *buf_data, int buf_length)
{  
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

