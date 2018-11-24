import logging.handlers
import requests
import datetime
import serial
import urllib
import json
import sys
import yaml
from P1 import read_telegram
from diff import diff

# Set up logging
log_level = logging.INFO
handler = logging.handlers.SysLogHandler(address = '/dev/log')
formatter = logging.Formatter('%(name)s [%(levelname)s] %(message)s')
handler.setLevel(log_level)
handler.setFormatter(formatter)
# Create logging instance
logger = logging.getLogger('pvoutput')
logger.setLevel(log_level)
logger.addHandler(handler)

# Load configuration YAML
fp = open('config.yaml','r')
cfg = yaml.load(fp)

# Check command line parameters
local = False           # Upload to PVOutput
verbose = False         # Verbose output
if(len(sys.argv) > 1):
    if('v' in sys.argv[1]):
	    verbose = True
    if('l' in sys.argv[1]):
        local = True

# Initialize variables
try:
    logger.debug('Trying to open serial port %s at baudrate %s [%s/%d/%d]' % (cfg['serial']['port'],cfg['serial']['baudrate'],cfg['serial']['parity'],cfg['serial']['bytesize'],cfg['serial']['stopbits']))
    ser = serial.Serial(cfg['serial']['port'], cfg['serial']['baudrate'], cfg['serial']['bytesize'], cfg['serial']['parity'], cfg['serial']['stopbits'])
except:
    logger.error('Unable to open serial port %s at baudrate %s [%s/%d/%d]' % (cfg['serial']['port'],cfg['serial']['baudrate'],cfg['serial']['parity'],cfg['serial']['bytesize'],cfg['serial']['stopbits']))
    sys.exit()

def main():
    # Start new session
    logger.debug('=== START OF SESSION ===')

    # Get solar and water data
    try:
        logger.debug('Accessing Main House web service at %s' % cfg['arduino_url']['mainhouse'])
        response = urllib.urlopen(cfg['arduino_url']['mainhouse'])
        data_json = json.loads(response.read())
        E_PV = data_json['E_PV']
        P_PV = data_json['P_PV']
        H2O = data_json['H2O']
		# Post-process water data
        H2O = diff(H2O, 'H2O')
    except:
        logger.error('No data received from Main House')
        sys.exit()

    # Get P1 data
	# Initialize variables
    E_net = -1
    P_net = -1
    itt = 0
    while ((E_net == -1) and (itt < cfg['p1']['retries'])):
        [P_net, E_net] = read_telegram(ser, logger, cfg['serial']['port'])
        if verbose:
            print('Power: %s' % P_net)
            print('Energy: %s' % E_net)
        itt += 1

    if(itt == cfg['p1']['retries']): # No valid value received within maximum number of tries
        logger.error('No valid P1 data after %d retries' % itt-1)
        sys.exit()

    # Compute Power and Energy Consumption
    E_cons = E_PV + E_net # v3
    P_cons = P_PV + P_net # v4

    # Get extended data
    try:
        logger.debug('Accessing Guard House web service at %s' % cfg['arduino_url']['mainhouse'])
        response = urllib.urlopen(cfg['arduino_url']['guardhouse'])
        data_json = json.loads(response.read())
        temp = data_json['Temperature']
        humi = data_json['Humidity']
        rain = data_json['Rain']
        soil_humi = data_json['Soil Humidity']
    except:
        logger.error('No data received from GuardHouse')
        temp = 0
        humi = 0
        rain = 0
        soil_humi = 0

    #  Prepare PVOutput headers
    headers = {
        'X-Pvoutput-Apikey': cfg['pvoutput']['key'],
        'X-Pvoutput-SystemId' : cfg['pvoutput']['sid']
    }

    # Prepare data
    date_str = datetime.datetime.today().strftime('%Y%m%d')
    time_str = datetime.datetime.today().strftime('%H:%M')

    # Logging data
    logger.debug('Date: %s' % date_str)
    logger.debug('Time: %s' % time_str)
    logger.info('Power Generation: %s W' % P_PV)
    logger.info('Power Consumption: %s W' % P_cons)
    logger.debug('Energy Generation: %s Wh' % E_PV)
    logger.debug('Energy Net Import: %s Wh' % E_net)
    logger.debug('Energy Consumption: %s Wh' % E_cons)
    logger.info('Water Consumption: %s liter' % H2O)
    logger.info('Temperature: %s C' % temp)
    logger.info('Humidity: %s %%' % humi)
    logger.info('Rain: %s ml' % rain)
    logger.info('Soil Humidity: %s %%' % soil_humi)

    # Prepare API data
    pvoutput_energy = cfg['pvoutput']['url'] + '?d=%s&t=%s&v1=%s&v2=%s&v3=%s&v4=%s&v7=%s&v8=%s&v9=%s&v11=%s&v12=%s&c1=1' % (date_str,time_str,E_PV,P_PV,E_cons,P_cons,temp,humi,H2O,rain,soil_humi)
    logger.debug('Request: %s' % pvoutput_energy)
    logger.debug('Headers: %s' % headers)

    # Upload
    if not local:
        r = requests.post(pvoutput_energy,headers=headers)
        logger.debug('Energy data upload: %s' % r.content)

    logger.debug('=== END OF SESSION ===')

if __name__ == "__main__":
    main()
