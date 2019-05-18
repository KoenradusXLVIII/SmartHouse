# Public packages
import requests
import datetime
import sys
import yaml
import os
import psutil

# Personal packages
import P1
import logger
import nebula
import arduino
import pushover
from diff import dx, dxdt
import openweathermap

# Check command line parameters
local = False  # Upload to PVOutput
verbose = False  # Verbose output
debug = False # Debug output
if len(sys.argv) > 1:
    if 'v' in sys.argv[1]:
        verbose = True
    if 'l' in sys.argv[1]:
        local = True
    if 'd' in sys.argv[1]:
        debug = True

# Load configuration YAML
path = os.path.dirname(os.path.realpath(__file__))
fp = open(path + '/config.yaml', 'r')
cfg = yaml.load(fp)

# Set up Pushover client
pushover_client = pushover.Client(**cfg['pushover'])

# Set up Nebula API client
nebula_client = nebula.Client(**cfg['nebula'])
nebula_client.set_level('WARNING')

# Set up Logger and attach Pushover client
log_client = logger.Client(name='pvoutput')
if debug:
    log_client.set_log_level('debug')
log_client.attach_pushover(pushover_client)
log_client.attach_nebula(nebula_client)

# Set up Arduino API clients
arduino_guardhouse = arduino.Client(**cfg['arduino']['guardhouse'])
arduino_mainhouse = arduino.Client(**cfg['arduino']['mainhouse'])

# Set up P1 client
p1_client = P1.Client('/dev/ttyUSB0')
if debug:
    p1_client.attach_logger(log_client)

# Set up OpenWeatherMap
owm_client = openweathermap.Client(**cfg['OWM'])


def main():
    # Get PV and Water data
    if verbose:
        print('Get PV and Water data...')
    data_mainhouse = arduino_mainhouse.get_all()
    if data_mainhouse is not None:
        # Post-process water data
        data_mainhouse['H2O'] = dx(data_mainhouse['H2O'], 'H2O')
    else:
        log_client.error('No data received from Main House')
        sys.exit()

    # Get P1 data
    if verbose:
        print('Get P1 data...')

    if not p1_client.read_telegram():
        log_client.error('No valid P1 data after %d retries' % p1_client.retries)
        sys.exit()

    # Get extended data
    if verbose:
        print('Get extended data...')
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
        'v3': data_mainhouse['E_PV'] + p1_client.energy,                # Energy Consumption [Wh]
        'v4': data_mainhouse['P_PV'] + p1_client.power,                 # Power Consumption [W]
    }
    if data_guardhouse is not None:
        payload.update({
            'v7': data_guardhouse['temp'],                              # Temperature [C]
            'v8': data_guardhouse['humi'],                              # Humidity [%]
            'v9': data_mainhouse['H2O'],                                # Water Consumption [l]
            'v11': data_guardhouse['rain'],                             # Precipitation [mm]
            'v12': data_guardhouse['soil_humi']                         # Soil Humidity [%]
        })

    # Post PVOutput payload
    if not local:
        if verbose:
            print('Post PVOutput payload..')
            print('PVOutput payload: %s' % payload)
        r = requests.post(cfg['pvoutput']['url'], headers=headers, params=payload)
        log_client.info('PVOutput energy data upload: %s' % r.text)
        log_client.debug('PVOutput payload: %s' % payload)

    # Prepare Nebula payload
    E_prod = data_mainhouse['E_PV']                                         # Solar Energy Production [Wh]
    E_cons = data_mainhouse['E_PV'] + p1_client.energy                      # Local Energy Consumption [Wh]
    P_prod = dxdt(E_prod, 'E_prod') * 3600                                  # Solar Energy Production [W]
    P_cons = dxdt(E_cons, 'E_cons') * 3600                                  # Local Energy Consumption [W]

    payload = {
        '6':  P_prod,                                                       # 5 minute average Solar Energy Production [W]
        '5':  P_cons,                                                       # 5-minute averaged Local Energy Consumption [W]
        '22': p1_client.energy / 1000,                                      # Net Energy Consumption [kWh]
        '46': E_cons / 1000,                                                # Local Energy Consumption [kWh]
        '47': E_prod / 1000,                                                # Solar Energy Production [kWh]
        '23': psutil.cpu_percent(),                                         # Current system-wide CPU utilization [%]
        '25': psutil.virtual_memory().percent,                              # Current memory usage [%]
        '26': psutil.disk_usage('/').percent,                               # Current disk usage [%]
        '27': psutil.sensors_temperatures()['bcm2835_thermal'][0].current,  # Current CPU temperature [C]
        '28': len(psutil.pids())                                            # Current number of active PIDs [-]
    }
    if data_guardhouse is not None:
        payload.update({
            '3':  data_guardhouse['temp'],                              # Temperature [C]
            '4':  data_guardhouse['humi'],                              # Humidity [%]
            '7':  data_mainhouse['H2O'],                                # Water Consumption [l]
            '8':  data_guardhouse['rain'],                              # Precipitation [mm]
            '9':  data_guardhouse['soil_humi'],                         # Soil Humidity [%]
            '10': data_guardhouse['door_state'],                        # Door State [Open/Closed]
            '11': data_guardhouse['light_state'],                       # Light State [On/Off]
            '13': data_guardhouse['valve_state'],                       # Valve State [Open/Closed]
            '16': data_guardhouse['alarm_mode'],                        # Alarm Mode [On/Off]
            '17': data_guardhouse['light_mode'],                        # Light Mode [Auto/Manual]
            '18': data_guardhouse['water_mode'],                        # Water Mode [Auto/Manual]
            '19': data_guardhouse['motor_light'],                       # Motor Light [On/Off]
            '20': data_guardhouse['day_night'],                         # Time of Day [Day/Night]
        })
    if owm_client.weather():
        payload.update({
            '80': owm_client.temp,
            '81': owm_client.humidity,
            '82': owm_client.wind,
            '83': owm_client.pressure
        })

    # Post Nebula payload
    if verbose:
            print('Post Nebula payload..')
            print('Nebula payload: %s' % payload)
    r = nebula_client.post_many(payload)
    nebula_client.info('Nebula upload: %s' % r.text)
    nebula_client.debug('Nebula payload: %s' % payload)


if __name__ == "__main__":
    main()
