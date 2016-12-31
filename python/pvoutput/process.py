#from influxdb import InfluxDBClient
import os
import logging
import sys
import csv
import requests
import datetime
import time
import serial

# Script variables
verbose = False
logging = False
base_path = '/home/pi/repository/python/pvoutput/'
logfile = base_path + 'output.log'

# Serial port configuration
port = '/dev/ttyACM0'
baudrate = '115200'
ser = serial.Serial(port, baudrate)

# PVOutput variables
pvoutput_key="d1b62a7d17dbebf167b98df9eb2f7c2188438d78"
pvoutput_sid="47507"
pvoutput_url="http://pvoutput.org/service/r2/addstatus.jsp"

# Configure logging
if(logging):
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S', filename=logfile)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


#
# Read data from Arduino
#

E_net = -1
E_PV = -1

while ((E_net < 0) or (E_PV < 0)):
    # Read serial data
    data_raw = str(ser.readline());
    data_raw = data_raw.strip();
    if(verbose):
        print(data_raw)
    if(data_raw.startswith("E_net")):
        data_array = data_raw.split()
        #print('Energy net: %s' % data_array[1])
        E_net = int(data_array[1])
    if(data_raw.startswith("E_PV")):
        data_array = data_raw.split()
        #print('Energy PV: %s' % data_array[1])
        # Write value to file
        E_PV = int(data_array[1]) # v1

#
# Upload to PVOutput
#

# Prepare headers
headers = {
    'X-Pvoutput-Apikey': pvoutput_key,
    'X-Pvoutput-SystemId' : pvoutput_sid
}

# Prepare data
date = datetime.datetime.today().strftime('%Y%m%d')
time = datetime.datetime.today().strftime('%H:%M')

E_cons = E_PV + E_net # v3

print 'Date: %s' % date
print 'Time: %s' % time
print 'Energy Generation: %s Wh' % E_PV
print 'Energy Consumption: %s Wh' % E_cons
if(logging):
    logging.info('Energy Generation: %s; Energy Consumption: %s' % (E_PV,E_cons))

# Prepare API data
pvoutput_energy = pvoutput_url + '?d=%s&t=%s&v1=%s&v3=%s&c1=1' % (date,time,E_PV,E_cons)
if(verbose):
    print pvoutput_energy

# Post API data
r = requests.post(pvoutput_energy,headers=headers)
if(logging):
    logging.info('Energy data upload: %s' % r.content)
