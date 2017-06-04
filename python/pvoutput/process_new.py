import logging
import logging.handlers
import requests
import datetime
import time
import serial
import urllib
import json
import sys
from P1 import read_telegram
from H2O import diff

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

# P1 configuration
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

def main():
    # Start new session
    logging.info('=== START OF SESSION ===')

    # Get solar and water data
    try:
        response = urllib.urlopen(mainhouse_url)
        data_json = json.loads(response.read())
        E_PV = data_json['E_PV']
        P_PV = data_json['P_PV']
        H2O = data_json['H2O']
    except:
        logging.error('No data received from Main House')
        E_PV = 0

    # Post-process water data
    H2O = diff(H2O)

    # Get P1 data
    E_net = -1
    itt = 0
    while ((E_net < 0) and (itt < p1_retries)):
        E_net = read_telegram(ser, logging)
        itt += 1

    if(itt == p1_retries): # No valid value received within maximum number of tries
        logging.error('No valid P1 data after %d retries' % itt-1)
        sys.exit()

    # Compute energy Consumption
    E_cons = E_PV + E_net # v3

    # Get extended data
    try:
        response = urllib.urlopen(guardhouse_url)
        data_json = json.loads(response.read())
        temp = data_json['Temperature']
        humi = data_json['Humidity']
        #door = data_json['Door state']
        #light = data_json['Light state']
    except:
        logging.error('No data received from GuardHouse')
        temp = 0
        humi = 0
        #door = 0
        #light = 0

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
    logging.info('Power Generation: %s W' % P_PV)
    logging.info('Energy Generation: %s Wh' % E_PV)
    logging.info('Energy Net Import: %s Wh' % E_net)
    logging.info('Energy Consumption: %s Wh' % E_cons)
    logging.info('Water Consumption: %s liter' % H2O)
    logging.info('Temperature: %s' % temp)
    logging.info('Humidity: %s' % humi)

    #logging.info('Door State: Open' if(door) else 'Door State: Closed')
    #logging.info('Light State: On' if(door) else 'Light State: Off')

    # Prepare API data
    pvoutput_energy = pvoutput_url + '?d=%s&t=%s&v1=%s&v3=%s&v7=%s&v8=%s&v9=%s&c1=1' % (date_str,time_str,E_PV,E_cons,temp,humi,H2O)
    #pvoutput_energy = pvoutput_url + '?d=%s&t=%s&v1=%s&v2=%s&v3=%s&v7=%s&v8=%s&v9=%s&c1=1' % (date_str,time_str,E_PV,P_PV,E_cons,temp,humi,H2O)
    logging.debug('Request: %s' % pvoutput_energy)

    # Upload
    r = requests.post(pvoutput_energy,headers=headers)

    # logging
    #logger.debug('Data received from Arduino: %s' % data_raw)
    logging.debug('Energy data upload: %s' % r.content)

    logging.info('=== END OF SESSION ===')

if __name__ == "__main__":
    main()
