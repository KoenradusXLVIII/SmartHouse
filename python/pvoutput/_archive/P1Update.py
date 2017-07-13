import serial
import sys
from PyCRC.CRC16 import CRC16
import re
import csv
import time
import os

# Serial port configuration
port = '/dev/ttyACM0'
baudrate = '115200'

# Initialize variables
ser = serial.Serial(port, baudrate)

# Script configuration
output_path = '/home/pi/repository/python/pvoutput/input/'
maximum_age = 60 # seconds
serial_to_terminal = False

def write_to_file(file,header,data):
    st = os.stat(output_path + file)
    file_age = time.time()-st.st_mtime
    if(file_age > maximum_age):
        print('[#] File is outdated, updating...')
        f = open(output_path + file,'wt')
        writer = csv.writer(f)
        writer.writerow([header])
        writer.writerow([str(data)])
        f.close

def main():
    # Start infinite cycle
    while(True):
        # Read serial data
        data_raw = str(ser.readline());
        data_raw = data_raw.strip();
        if(serial_to_terminal):
            print(data_raw)
        if(data_raw.startswith("E_net")):
            data_array = data_raw.split()
            print('Energy net: %s' % data_array[1])
            # Write value to file
            write_to_file('P1new.csv','Energy net',data_array[1])
        if(data_raw.startswith("E_PV")):
            data_array = data_raw.split()
            print('Energy PV: %s' % data_array[1])
            # Write value to file
            write_to_file('growattnew.csv','Energy PV',data_array[1])

if __name__ == "__main__":
    main()
