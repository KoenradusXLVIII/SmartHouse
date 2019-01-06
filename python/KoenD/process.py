# Public packages
import csv
import psutil
import datetime
import sqlite3
import yaml
import os

# Private packages
import logger
import nebula
from diff import diff

# Load configuration YAML
path = os.path.dirname(os.path.realpath(__file__))
fp = open(path + '/config.yaml', 'r')
cfg = yaml.load(fp)

# Set up Nebula API client
nebula_client = nebula.Client(**cfg['nebula'])

# Get P1 data through Domoticz
db = sqlite3.connect(cfg['domoticz']['db'])
cursor = db.cursor()
cursor.execute("SELECT * FROM MultiMeter ORDER BY Date DESC LIMIT 1")
result = cursor.fetchone()
E_net = (result[1] + result[5] - result[2] - result[6])/1000.0

# Get SMA data
SMA_file = '/home/pi/smadata/%d/MyPlant-Spot-SingleLine.csv' % datetime.datetime.now().year
try:
    with open(SMA_file, 'r') as fp:
        reader = csv.reader(fp, delimiter=';')
        SMA_data = next(reader)
        for key, value in enumerate(SMA_data):
            SMA_data[key] = SMA_data[key].replace(',', '.')
except FileNotFoundError:
    nebula_client.error ('SMA data file not found! [%s]' % SMA_file)

# Prepare Nebula payload
E_PV = float(SMA_data[23])                                              # Solar Energy Production [kWh]
E_cons = E_PV + E_net                                                   # Local Energy Consumption [kWh]
P_prod = diff(E_PV, 'E_PV') * (60 / 5) * 1000                           # 5 minute average Solar Energy Production [W]
P_net = diff(E_net, 'E_net') * (60 / 5) * 1000                          # 5-minute average Net ENergy Consumption [W]
P_cons = P_prod + P_net

payload = {
    '32': P_net,                                                            # Net Power Consumption [W]
    '30': E_net,                                                            # Net Energy Consumption [kWh]
    '43': P_cons,                                                           # Local Power Consumption [W]
    '33': P_prod,                                                           # Solar Power Production [W]
    '34': SMA_data[22],                                                     # Solar Energy Production Today [kWh]
    '35': SMA_data[24],                                                     # Inverter Frequency [Hz]
    '36': SMA_data[30],                                                     # Inverter Temperature [C]
    '37': E_PV,                                                             # Solar Energy Production Total [kWh]
    '42': psutil.cpu_percent(),                                             # Current system-wide CPU utilization [%]
    '41': psutil.virtual_memory().percent,                                  # Current memory usage [%]
    '40': psutil.disk_usage('/').percent,                                   # Current disk usage [%]
    '39': psutil.sensors_temperatures()['bcm2835_thermal'][0].current,      # Current CPU temperature [C]
    '38': len(psutil.pids())                                                # Current number of active PIDs [-]
}

# Post Nebula payload
r = nebula_client.post_many(payload)
nebula_client.info('Nebula upload: %s' % r.text)
nebula_client.debug('Nebula payload: %s' % payload)
