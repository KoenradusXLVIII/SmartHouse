import serial
import sys
from PyCRC.CRC16 import CRC16
import re
import csv
import time
import os

# Serial port configuration
port = '/dev/ttyUSB0'
baudrate = '115200'
parity = 'N'
bytesize = 8
stopbits = 1

# Smart meter configuration
serial_number = 'XMX5LGBBFG1009050373'
eot_char = '!' # End of transmission character
CRC_length = 4 # 4 byte hexadecimal CRC16 value
telegram_length = 23 # lines
OBIS = [
    ['Energy import [low]', '1-0:1.8.1','(\d-\d):(\d\.?)+\((\d{6}\.\d{3})\*kWh\)'],
    ['Energy import [high]', '1-0:1.8.2','(\d-\d):(\d\.?)+\((\d{6}\.\d{3})\*kWh\)'],
    ['Energy export [low]', '1-0:2.8.1','(\d-\d):(\d\.?)+\((\d{6}\.\d{3})\*kWh\)'],
    ['Energy export [high]', '1-0:2.8.2','(\d-\d):(\d\.?)+\((\d{6}\.\d{3})\*kWh\)']
]

# Initialize variables
ser = serial.Serial(port, baudrate, bytesize, parity, stopbits)

# Functions
def read_telegram():
    # Initialize local variables
    itt = 0
    CRC_data = ''
    data = []

    # Start receiving raw data
    data_raw = str(ser.readline())
    while (serial_number not in data_raw):
        data_raw = str(ser.readline())
        itt += 1
        if (itt >= telegram_length):
            print('[#] Invalid telegram')
            return -1

    # Start of transmission detected
    print('[#] Start of transmission detected')
    data.append(data_raw.strip())
    CRC_data += data_raw

    # Read appropriate amount of lines
    while (data_raw.startswith(eot_char) == False):
        data_raw = str(ser.readline())
        data.append(data_raw.strip())
        if (data_raw.startswith(eot_char)):
            print('[#] End of transmission detected')
        else:
            CRC_data += data_raw

    # Check for options
    if (len(sys.argv) > 1):
        # Output data if verbose option
        if (sys.argv[1] == '-v'):
            print('[#] Data received: %s' % data)

    # Verify CRC
    CRC_rec = data[len(data)-1]
    CRC_data += '!'
    if(CRC_rec.startswith(eot_char)):
        CRC = hex(CRC16().calculate(CRC_data))
        CRC = CRC[2:].upper()
        CRC_rec = CRC_rec[1:] # Remove '!' for displayed CRC

        if (CRC == CRC_rec):
            print('[#] Valid data, CRC match: 0x%s' % CRC)

            # Parsa data and compute net energy usage
            energy = 0.0
            for line in range (1,len(data)):
                for desc, ref, regex in OBIS:
                    if(data[line].startswith(ref)):
                        m = re.search(regex,data[line])
                        print('[#] %s: %s' % (desc,m.group(3)))
                        if(data[line].startswith('1-0:1.')):
                            energy += float(m.group(3))
                        else:
                            energy -= float(m.group(3))

            # Return energy value [kWh]
            print('[#] Valid energy value received: %f' % energy)
            return energy
        else:
            # Message incorrect, CRC mismatch
            print('[#] CRC mismatch: 0x%s / 0x%s' % (CRC,CRC_rec))
            return -1

def main():
    # Initialize variables
    itt = 0
    energy_valid = -1

    # Get first valid value
    while(energy_valid < 0):
        energy_valid = read_telegram()

    # Start infinite cycle
    while(True):
        itt += 1
        energy = read_telegram()
        if(energy >= 0):
            print('[#] Valid message received after %d retries' % (itt-1))
            energy_valid = energy
            itt = 0
        else:
            print('[#] Invalid message received, retrying... [%d]' % itt)

if __name__ == "__main__":
    main()
