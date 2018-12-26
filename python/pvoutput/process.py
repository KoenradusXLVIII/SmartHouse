# Public packages
import requests
import datetime
import sys
import yaml
import os

# Private packages
import P1
import logger
import nebula
import arduino
import pushover
from diff import diff # TODO

# Load configuration YAML
path = os.path.dirname(os.path.realpath(__file__))
fp = open(path + '/config.yaml', 'r')
cfg = yaml.load(fp)

# Set up Pushover client
pushover_client = pushover.Client(cfg['pushover']['token'], cfg['pushover']['user'])

# Set up Logger and attach Pushover client
log_client = logger.Client(name='pvoutput')
log_client.attach_pushover(pushover_client)

# Set up Nebula API client
nebula_client = nebula.Client(cfg['nebula']['url'],cfg['nebula']['key'])

# Set up Arduino API clients
arduino_guardhouse = arduino.Client(cfg['arduino']['guardhouse']['ip'])
arduino_mainhouse = arduino.Client(cfg['arduino']['mainhouse']['ip'])

# Set up P1 client
p1_client = P1.Client('/dev/ttyUSB0')
p1_client.read_telegram()

# Check command line parameters
local = False  # Upload to PVOutput
verbose = False  # Verbose output
if (len(sys.argv) > 1):
    if 'v' in sys.argv[1]:
        verbose = True
    if 'l' in sys.argv[1]:
        local = True


def main():
    # Get PV and Water data
    data_mainhouse = arduino_mainhouse.get_all()
    if data_mainhouse is not None:
        # Post-process water data
        data_mainhouse['H2O'] = diff(data_mainhouse['H2O'], 'H2O')
    else:
        log_client.error('No data received from Main House')
        sys.exit()

    # Get P1 data
    itt = 0
    while not p1_client.read_telegram() and itt < cfg['P1']['retries']:
        itt += 1

    if itt == cfg['P1']['retries']:  # No valid value received within maximum number of tries
        log_client.error('No valid P1 data after %d retries' % itt - 1)
        sys.exit()

    # Get extended data
    data_guardhouse = arduino_guardhouse.get_all()
    if data_guardhouse is None:
        log_client.error('No data received from GuardHouse')

    #  Prepare PVOutput headers
    headers = {
        'X-Pvoutput-Apikey': cfg['pvoutput']['key'],
        'X-Pvoutput-SystemId': cfg['pvoutput']['sid']
    }

    # Prepare PVOutput payload
    payload = {
        'd': datetime.datetime.today().strftime('%Y%m%d'),              # Date [yyyymmdd]
        't': datetime.datetime.today().strftime('%H:%M'),               # Time [hh:mm]
        'c1': 1,                                                        # Cumulative Flag [-]
        'v1': data_mainhouse['E_PV'],                                   # Energy Generation [Wh]
        'v2': data_mainhouse['P_PV'],                                   # Power Generation [W]
        'v3': data_mainhouse['E_PV'] + p1_client.get_energy(),          # Energy Consumption [Wh]
        'v4': data_mainhouse['P_PV'] + p1_client.get_power(),           # Power Consumption [W]
    }
    if data_guardhouse is not None:
        payload.update({
            'v7': data_guardhouse['temp'],                              # Temperature [C]
            'v8': data_guardhouse['humi'],                              # Humidity [%]
            'v9': data_mainhouse['H2O'],                                # Water Consumption [l]
            'v11': data_guardhouse['rain'],                             # Precipitation [mm]
            'v12': data_guardhouse['soil_humi']                         # Soil Humidity [%]
        })
    log_client.debug('PVOutput payload: %s' % payload)
    if verbose:
        print('PVOutput payload: %s' % payload)

    # Post PVOutput payload
    if not local:
        r = requests.post(cfg['pvoutput']['url'], headers=headers, params=payload)
        log_client.info('Energy data upload: %s' % r.content)

    # Prepare Nebula payload
    payload = {
        '6':  data_mainhouse['P_PV'],                                   # Power Generation [W]
        '5':  data_mainhouse['P_PV'] + p1_client.get_power(),           # Power Consumption [W]
        '22': p1_client.get_energy()                                    # Net Energy Consumption [W]
    }
    if data_guardhouse is not None:
        payload.update({
            '3':  data_guardhouse['temp'],                              # Temperature [C]
            '4':  data_guardhouse['humi'],                              # Humidity [%]
            '7':  data_mainhouse['H2O'],                                # Water Consumption [l]
            '8':  data_guardhouse['rain'],                              # Precipitation [mm]
            '9':  data_guardhouse['soil_humi'],                         # Soil Humidity [%]
            '10': data_guardhouse['door_state'],                        # Door State [-]
            '11': data_guardhouse['light_state'],                       # Light State [On/Off]
            '13': data_guardhouse['valve_state'],                       # Valve State [Open/Close]
            '16': data_guardhouse['alarm_mode'],                        # Alarm Mode [On/Off]
            '17': data_guardhouse['light_mode'],                        # Light Mode [Auto/Manual]
            '18': data_guardhouse['water_mode'],                        # Water Mode [Auto/Manual]
            '19': data_guardhouse['motor_light'],                       # Motor Light [On/Off]
            '20': data_guardhouse['day_night'],                         # Time of Day [Day/Night]
        })
    log_client.debug('PVOutput payload: %s' % payload)
    if verbose:
        print('PVOutput payload: %s' % payload)

    # Post Nebula payload
    nebula_client.add_many(payload)
    nebula_client.post_payload()

if __name__ == "__main__":
    main()
