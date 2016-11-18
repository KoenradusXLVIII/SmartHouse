#from influxdb import InfluxDBClient
import os
import logging
import sys
import csv
import requests
import datetime
import time

# Script variables
# Directories
base_path = '/home/pi/repository/python/pvoutput/'
input_path = base_path + 'input/'
# logging
logfile = base_path + 'output.log'
# P1
#P1_script = 'P1Read.py'
P1_data = 'P1new.csv'
# Growatt
growatt_data = 'growattnew.csv'
growatt_refresh = 500 # seconds

# PVOutput variables
pvoutput_key="d1b62a7d17dbebf167b98df9eb2f7c2188438d78"
pvoutput_sid="47507"
pvoutput_url="http://pvoutput.org/service/r2/addstatus.jsp"

# Configure logging
logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S', filename=logfile)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Initialize variables
keys = []
values = []

# Check to see who's calling
'''
if (len(sys.argv) == 2):
    if (sys.argv[1] == 'cron'):
        logging.debug('PVOutput script called from Cron job')
        st = os.stat(input_path + growatt_data)
        growatt_age = (time.time()-st.st_mtime)
        if(growatt_age < growatt_refresh):
            logging.debug('Nothing to do; Growatt script uploaded already')
            sys.exit()
    elif (sys.argv[1] == 'growatt'):
        logging.debug('PVOutput script called from Growatt script')
    else:
        logging.warning('Invalid argument')
        sys.exit()
else:
    logging.warning('Invalid argument count: %d' % len(sys.argv))
    sys.exit()

# Do live P1 read-out
#logging.debug('Perform P1 read-out')
#os.system('python %s%s' % (base_path,P1_script))
'''

# Parse P1 data
with open(input_path + P1_data,'rb') as csvfile:
    reader = csv.reader(csvfile)
    row = next(reader)
    for item in row:
        keys.append(item)
    row = next(reader)
    for item in row:
        values.append(item)

# Parse Growatt data
with open(input_path + growatt_data,'rb') as csvfile:
    reader = csv.reader(csvfile)
    row = next(reader)
    for item in row:
        keys.append(item)
    row = next(reader)
    for item in row:
        values.append(item)

# Upload to PVOutput
headers = {
    'X-Pvoutput-Apikey': pvoutput_key,
    'X-Pvoutput-SystemId' : pvoutput_sid
}

# Prepare data
date = datetime.datetime.today().strftime('%Y%m%d')
time = datetime.datetime.today().strftime('%H:%M')
data = dict(zip(keys,values))

# Power data
#power_import = int((float(data['Power import']))*1000)
#power_export = int((float(data['Power export']))*1000)
#power_generation = float(data['Power PV']) # v2
#power_consumption = power_generation + power_import - power_export # v4

# Energy data
#energy_import = int((float(data['Energy import [low]']) + float(data['Energy import [high]']))*1000)
#energy_export = int((float(data['Energy export [low]']) + float(data['Energy export [high]']))*1000)
energy_net_consumption = power_export = int(data['Energy net'])
energy_generation = int(data['Energy PV']) # v1
energy_consumption = energy_generation + energy_net_consumption # v3

print 'Date: %s' % date
print 'Time: %s' % time
print 'Energy Generation: %s Wh' % energy_generation
#print 'Power Generation: %s W' % power_generation
print 'Energy Consumption: %s Wh' % energy_consumption
#print 'Power Consumption: %s W' % power_consumption
logging.info('Energy Generation: %s; Energy Consumption: %s' % (energy_generation,energy_consumption))

# Prepare API data
pvoutput_energy = pvoutput_url + '?d=%s&t=%s&v1=%s&v3=%s&c1=1' % (date,time,energy_generation,energy_consumption)
#pvoutput_power = pvoutput_url + '?d=%s&t=%s&v2=%s' % (date,time,power_generation)
print pvoutput_energy
#print pvoutput_power

# Post API data
r = requests.post(pvoutput_energy,headers=headers)
logging.info('Energy data upload: %s' % r.content)
#r = requests.post(pvoutput_power,headers=headers)
#logging.info('Power data upload: %s' % r.content)
