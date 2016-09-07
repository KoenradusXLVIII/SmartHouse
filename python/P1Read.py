import serial
import sys
from PyCRC.CRC16 import CRC16
import re
import csv

# Serial port configuration
port = '/dev/ttyACM0'
baudrate = '115200'

# Smart meter configuration
serial_number = 'XMX5LGBBFG1009050373'
eot_char = '!' # End of transmission character
CRC_length = 4 # 4 byte hexadecimal CRC16 value
telegram_length = 23 # lines
OBIS = [
    ['Power received [low]', '1-0:1.8.1','(\d-\d):(\d\.?)+\((\d{6}\.\d{3})\*kWh\)'],
    ['Power received [high]', '1-0:1.8.2','(\d-\d):(\d\.?)+\((\d{6}\.\d{3})\*kWh\)'],
    ['Power delivered [low]', '1-0:2.8.1','(\d-\d):(\d\.?)+\((\d{6}\.\d{3})\*kWh\)'],
    ['Power delivered [high]', '1-0:2.8.2','(\d-\d):(\d\.?)+\((\d{6}\.\d{3})\*kWh\)']
]

# Script configuration
timeout = 2*telegram_length
retries = 10

# Initialize variables
ser = serial.Serial(port, baudrate)

# Functions
def read_telegram(data):
    # Initialize local variables
    itt = 0
    CRC_data = ''

    # Start receiving raw data
    data_raw = str(ser.readline())
    while (serial_number not in data_raw):
        data_raw = str(ser.readline())
        itt += 1
        if (itt >= timeout):
            print('[#] ERROR: Invalid data from meter')
            sys.exit()

    # Start of transmission detected
    print('[#] Start of transmission detected')
    data.append(data_raw.strip())
    CRC_data += data_raw
    #print(data_raw)

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
            return True
        else:
            # Not the entire message is correct
            # However we don't need all lines to be Valid
            itt = 0

            print('[#] CRC mismatch: 0x%s / 0x%s' % (CRC,CRC_rec))
            for line in range (1,len(data)-1):
                for desc, ref, regex in OBIS:
                    if(data[line].startswith(ref)):
                        if (re.match(regex,data[line])) is None:
                            print('[#] A required value is invalid: %s' % data[line])
                            return False
                        else:
                            itt += 1

    if (itt == len(OBIS)):
        # All required values are valid
        return True
    else:
        return False

itt = 0
while (itt < retries):
    data = []
    if(read_telegram(data)):
        print('[#] Valid message received after %d retries' % (itt+1))

        # Write to CSV
        f = open('/home/pi/repository/python/P1.csv','wt')
        writer = csv.writer(f)
        # Write header
        header = []
        for desc, ref, regex in OBIS:
            header.append(desc)
        writer.writerow(header)

        data_CSV = []
        for line in range (1,len(data)-1):
            for desc, ref, regex in OBIS:
                if(data[line].startswith(ref)):
                    m = re.search(regex,data[line])
                    print('[#] %s: %s' % (desc,m.group(3)))
                    data_CSV.append(m.group(3))
        # Write data
        writer.writerow(data_CSV)

        # Close CSV file
        f.close
        sys.exit()
    else:
        itt += 1
        print('[#] Invalid message received, retrying... [%d/%d]' % (itt,retries))

print('[#] No valid message received [%d/%d]' % (itt,retries))
