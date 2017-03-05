import logging
import logging.handlers
import requests
import datetime
import time
import serial
import re
import urllib
import json
import sys
from PyCRC.CRC16 import CRC16

# Script variables
#verbose = True
base_path = '/media/usb/log/'
logfile = base_path + 'output.log'
log_level = logging.INFO
#interval = 300 # seconds

# Configure logging
logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=log_level, datefmt='%Y-%m-%d %H:%M:%S', filename=logfile)

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
p1_retries = 5

# Initialize variables
try:
    ser = serial.Serial(port, baudrate, bytesize, parity, stopbits)
except:
    logging.error('Unable to open serial port: %s' % port)
    sys.exit()

# Guardhouse configuration
guardhouse_url = "http://192.168.1.112/all"

# Mainhouse configuration
mainhouse_url = "http://192.168.1.113/all"

# PVOutput variables
pvoutput_key="d1b62a7d17dbebf167b98df9eb2f7c2188438d78"
pvoutput_sid="47507"
pvoutput_url="http://pvoutput.org/service/r2/addstatus.jsp"

def read_telegram():
    # Initialize local variables
    itt = 0
    CRC_data = ''
    data = []

    # Start receiving raw data
    try:
        data_raw = str(ser.readline())
    except:
        logging.error('Unable to read from serial port: %s' % port)
        sys.exit()

    while (serial_number not in data_raw):
        try:
            data_raw = str(ser.readline())
        except:
            logging.error('Unable to read from serial port: %s' % port)
            sys.exit()
        itt += 1
        if (itt >= telegram_length):
            logging.warning('Invalid telegram')
            return -1

    # Start of transmission detected
    logging.info('Start of transmission detected')
    data.append(data_raw.strip())
    logging.debug('Data received: %s' % data_raw.strip())
    CRC_data += data_raw

    # Read appropriate amount of lines
    while (data_raw.startswith(eot_char) == False):
        try:
            data_raw = str(ser.readline())
        except:
            logging.error('Unable to read from serial port: %s' % port)
            sys.exit()
        data.append(data_raw.strip())
        if (data_raw.startswith(eot_char)):
            logging.info('End of transmission detected')
        else:
            CRC_data += data_raw

    # Check for options
    if (len(sys.argv) > 1):
        # Output data if verbose option
        if (sys.argv[1] == '-v'):
            print('Data received: %s' % data)

    # Verify CRC
    CRC_rec = data[len(data)-1]
    CRC_data += '!'
    if(CRC_rec.startswith(eot_char)):
        CRC = hex(CRC16().calculate(CRC_data))
        CRC = CRC[2:].upper()
        CRC_rec = CRC_rec[1:] # Remove '!' for displayed CRC

        if (CRC == CRC_rec):
            logging.info('Valid data, CRC match: 0x%s' % CRC)

            # Parsa data and compute net energy usage
            energy = 0.0
            for line in range (1,len(data)):
                for desc, ref, regex in OBIS:
                    if(data[line].startswith(ref)):
                        m = re.search(regex,data[line])
                        logging.debug('%s: %s' % (desc,m.group(3)))
                        if(data[line].startswith('1-0:1.')):
                            energy += float(m.group(3))
                        else:
                            energy -= float(m.group(3))

            # Return energy value [Wh]
            energy *= 1000
            logging.info('Valid energy value received: %f Wh' % energy)
            return int(energy)
        else:
            # Message incorrect, CRC mismatch
            logging.warning('CRC mismatch: 0x%s / 0x%s' % (CRC,CRC_rec))
            return -1

def main():
    # Start new session
    logging.info('=== START OF SESSION ===')

    # Get solar data
    E_PV = 0

    # Get P1 data
    E_net = -1
    itt = 0
    while ((E_net < 0) and (itt < p1_retries)):
        E_net = read_telegram()
        itt += 1

    if(itt == p1_retries): # No valid value received within maximum number of tries
        logging.error('No valid P1 data after %d retries' % itt-1)
        sys.exit()

    # Compute energy Consumption
    E_cons = E_PV + E_net # v3

    # Get extended data
    try:
        response = urllib.urlopen(guardhouse_url)
    except:
        logging.error('No data received from GuardHouse')
    data_json = json.loads(response.read())

    #  Prepare PVOutput headers
    headers = {
        'X-Pvoutput-Apikey': pvoutput_key,
        'X-Pvoutput-SystemId' : pvoutput_sid
    }

    # Prepare data
    date_str = datetime.datetime.today().strftime('%Y%m%d')
    time_str = datetime.datetime.today().strftime('%H:%M')

    # Logging data
    logging.debug('Date: %s' % date_str)
    logging.debug('Time: %s' % time_str)
    logging.info('Energy Generation: %s Wh' % E_PV)
    logging.info('Energy Net Import: %s Wh' % E_net)
    logging.info('Energy Consumption: %s Wh' % E_cons)
    logging.info('Temperature: %s' % data_json['Temperature'])
    logging.info('Humidity: %s' % data_json['Humidity'])

    # Prepare API data
    pvoutput_energy = pvoutput_url + '?d=%s&t=%s&v1=%s&v3=%s&v7=%s&v8=%s&c1=1' % (date_str,time_str,E_PV,E_cons,data_json['Temperature'],data_json['Humidity'])
    logging.debug('Request: %s' % pvoutput_energy)

    # Upload
    r = requests.post(pvoutput_energy,headers=headers)

    # logging
    #logger.debug('Data received from Arduino: %s' % data_raw)
    logging.debug('Energy data upload: %s' % r.content)

    logging.info('=== END OF SESSION ===')

if __name__ == "__main__":
    main()
