import logging
import logging.handlers
import requests
import datetime
import time
import serial
import re
import urllib
import json

# Script variables
verbose = False
base_path = '/home/pi/repository/python/pvoutput/'
logfile = base_path + 'output.log'
log_level = logging.INFO
interval = 300 # seconds

# Serial port configuration
port = '/dev/ttyACM0'
baudrate = '115200'
ser = serial.Serial(port, baudrate)

# Guardhouse configuration
url = "http://192.168.1.112/"

# PVOutput variables
pvoutput_key="d1b62a7d17dbebf167b98df9eb2f7c2188438d78"
pvoutput_sid="47507"
pvoutput_url="http://pvoutput.org/service/r2/addstatus.jsp"

# Configure logging
logger = logging.getLogger('PVOutput_Logger')
logger.setLevel(log_level)
# Add handler to the logger
handler = logging.handlers.SysLogHandler('/dev/log')
# Add syslog format to the handler
formatter = logging.Formatter('Python: { "loggerName":"%(name)s", "asciTime":"%(asctime)s", "pathName":"%(pathname)s", "logRecordCreationTime":"%(created)f", "functionName":"%(funcName)s", "levelNo":"%(levelno)s", "lineNo":"%(lineno)d", "time":"%(msecs)d", "levelName":"%(levelname)s", "message":"%(message)s"}')
handler.formatter = formatter
logger.addHandler(handler)

# Initialize variables
regex = 'E_(net|PV): (\d{1,})'
start_time = 0

while(True):
    # Initialize Arduino variables
    E_net = -1
    E_PV = -1

    # Wait to receive two valid values
    while ((E_net < 0) or (E_PV < 0)):
        # Read serial data
        data_raw = str(ser.readline())
        data_raw = data_raw.strip()
        if(verbose):
            print(data_raw)

        # Validate data
        m = re.search(regex,data_raw)
        if(m):
            if(m.group(1) == 'net'):
                E_net = int(m.group(2))
            if(m.group(1) == 'PV'):
                E_PV =  int(m.group(2)) # v1
        else:
            logger.warning('Received invalid data: %s' % data_raw)
    E_cons = E_PV + E_net # v3

    # Get extended data
    response = urllib.urlopen(url)
    data_json = json.loads(response.read())

    # Prepare PVOutput headers
    headers = {
        'X-Pvoutput-Apikey': pvoutput_key,
        'X-Pvoutput-SystemId' : pvoutput_sid
    }

    # Prepare data
    date_str = datetime.datetime.today().strftime('%Y%m%d')
    time_str = datetime.datetime.today().strftime('%H:%M')

    if(verbose):
        print 'Date: %s' % date_str
        print 'Time: %s' % time_str
        print 'Energy Generation: %s Wh' % E_PV
        print 'Energy Net Import: %s Wh' % E_net
        print 'Energy Consumption: %s Wh' % E_cons
        print 'Temperature: %s' % data_json['Temperature']
        print 'Humidity: %s' % data_json['Humidity']

    # Prepare API data
    pvoutput_energy = pvoutput_url + '?d=%s&t=%s&v1=%s&v3=%s&v7=%s&v8=%s&c1=1' % (date_str,time_str,E_PV,E_cons,data_json['Temperature'],data_json['Humidity'])
    if(verbose):
        print pvoutput_energy

    # Post API data every 5 minutes
    elapsed_time = time.time() - start_time
    if(elapsed_time >= interval):
        start_time = time.time()

        # Upload
        r = requests.post(pvoutput_energy,headers=headers)

        # logging
        logger.debug('Data received from Arduino: %s' % data_raw)
        logger.info('Energy Generation: %s; Energy Net Consumption: %s; Energy Consumption: %s' % (E_PV,E_net,E_cons))
        logger.info('Energy data upload: %s' % r.content)
    else:
        if(verbose):
            print 'Time to wait: %d seconds' % (interval-elapsed_time)
