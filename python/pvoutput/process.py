import requests
import datetime
import serial
import urllib
import json
import sys
import yaml
import os
from P1 import read_telegram
from diff import diff
import logger
import nebula

# Set up logger
log_client = logger.Client(name='pvoutput')

# Load configuration YAML
path = os.path.dirname(os.path.realpath(__file__))
fp = open(path + '/config.yaml', 'r')
cfg = yaml.load(fp)

# Set up Nebula API
nebula_client = nebula.Client(cfg['nebula']['url'])

# Check command line parameters
local = False  # Upload to PVOutput
verbose = False  # Verbose output
if (len(sys.argv) > 1):
    if ('v' in sys.argv[1]):
        verbose = True
    if ('l' in sys.argv[1]):
        local = True

# Initialize variables
try:
    log_client.debug('Trying to open serial port %s at baudrate %s [%s/%d/%d]' % (
    cfg['serial']['port'], cfg['serial']['baudrate'], cfg['serial']['parity'], cfg['serial']['bytesize'],
    cfg['serial']['stopbits']))
    ser = serial.Serial(cfg['serial']['port'], cfg['serial']['baudrate'], cfg['serial']['bytesize'],
                        cfg['serial']['parity'], cfg['serial']['stopbits'])
except:
    log_client.error('Unable to open serial port %s at baudrate %s [%s/%d/%d]' % (
    cfg['serial']['port'], cfg['serial']['baudrate'], cfg['serial']['parity'], cfg['serial']['bytesize'],
    cfg['serial']['stopbits']))
    sys.exit()


def main():
    # Start new session
    log_client.debug('=== START OF SESSION ===')

    # Get solar and water data
    try:
        log_client.debug('Accessing Main House web service at %s' % cfg['arduino_url']['mainhouse'])
        response = urllib.urlopen(cfg['arduino_url']['mainhouse'])
        data_json = json.loads(response.read())
        E_PV = data_json['E_PV']
        P_PV = data_json['P_PV']
        H2O = data_json['H2O']
        # Post-process water data
        H2O = diff(H2O, 'H2O')
    except:
        log_client.error('No data received from Main House')
        sys.exit()

    # Get P1 data
    # Initialize variables
    E_net = -1
    P_net = -1
    itt = 0
    while (E_net == -1) and (itt < cfg['p1']['retries']):
        [P_net, E_net] = read_telegram(ser, log_client, cfg['serial']['port'])
        if verbose:
            print('Power: %s' % P_net)
            print('Energy: %s' % E_net)
        itt += 1

    if itt == cfg['p1']['retries']:  # No valid value received within maximum number of tries
        log_client.error('No valid P1 data after %d retries' % itt - 1)
        sys.exit()

    # Compute Power and Energy Consumption
    E_cons = E_PV + E_net  # v3
    P_cons = P_PV + P_net  # v4

    # Get extended data
    try:
        log_client.debug('Accessing Guard House web service at %s' % cfg['arduino_url']['mainhouse'])
        response = urllib.urlopen(cfg['arduino_url']['guardhouse'])
        data_json = json.loads(response.read())
        temp = data_json['temp']
        humi = data_json['humi']
        rain = data_json['rain']
        soil_humi = data_json['soil_humi']
    except:
        log_client.error('No data received from GuardHouse')
        temp = 0
        humi = 0
        rain = 0
        soil_humi = 0

    #  Prepare PVOutput headers
    headers = {
        'X-Pvoutput-Apikey': cfg['pvoutput']['key'],
        'X-Pvoutput-SystemId': cfg['pvoutput']['sid']
    }

    # Prepare data
    date_str = datetime.datetime.today().strftime('%Y%m%d')
    time_str = datetime.datetime.today().strftime('%H:%M')

    # Logging data
    log_client.debug('Date: %s' % date_str)
    log_client.debug('Time: %s' % time_str)
    log_client.debug('Power Generation: %s W' % P_PV)
    log_client.debug('Power Consumption: %s W' % P_cons)
    log_client.debug('Energy Generation: %s Wh' % E_PV)
    log_client.debug('Energy Net Import: %s Wh' % E_net)
    log_client.debug('Energy Consumption: %s Wh' % E_cons)
    log_client.debug('Water Consumption: %s liter' % H2O)
    log_client.debug('Temperature: %s C' % temp)
    log_client.debug('Humidity: %s %%' % humi)
    log_client.debug('Rain: %s ml' % rain)
    log_client.debug('Soil Humidity: %s %%' % soil_humi)

    # Prepare API data
    pvoutput_energy = cfg['pvoutput']['url'] +\
                      '?d=%s&t=%s&v1=%s&v2=%s&v3=%s&v4=%s&v7=%s&v8=%s&v9=%s&v11=%s&v12=%s&c1=1' % \
                      (date_str, time_str, E_PV, P_PV, E_cons, P_cons, temp, humi, H2O, rain, soil_humi)
    log_client.debug('Request: %s' % pvoutput_energy)
    log_client.debug('Headers: %s' % headers)

    # Upload
    if not local:
        r = requests.post(pvoutput_energy, headers=headers)
        log_client.info('Energy data upload: %s' % r.content)

    # Nebula
    nebula_client.set_meas(3, temp)
    nebula_client.set_meas(4, humi)
    nebula_client.set_meas(5, P_cons)
    nebula_client.set_meas(6, P_PV)

    log_client.debug('=== END OF SESSION ===')


if __name__ == "__main__":
    main()
