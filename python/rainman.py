import urllib
import json
import datetime as dt
import logging
import sys
from time import sleep

# Weather Underground API
base = "http://api.wunderground.com/api/f0c3002dabae8c04/"
city = "/q/NL/Eindhoven.json"

# SmartHouse API
sprinkler_on = "http://192.168.1.112/water_mode/manual"
sprinkler_off = "http://192.168.1.112/water_mode/auto"

# Settings
# Limits
lim_high_temp = 30 # C
lim_med_temp = 25 # C
lim_low_temp = 20 # C
lim_qpf_allday = 3 # mm
lim_qpf_allweek = 3 # mm

# Sprinkler modes
high_duration = 8 # mins
med_duration = 8 # mins
low_duration = 10 # mins
high_times = [8, 11, 14, 17, 20]
med_times = [8, 13, 18]
low_times = [8, 18]

# Define variables
qpf_allday = []
qpf_allweek = 0
sprinkler_times = []
sprinkler_duration = 0
sprinkler_mode = 'off'

# Configure logging
base_path = '/media/usb/log/'
logfile = base_path + 'output.log'
log_level = logging.INFO
logging.basicConfig(format='%(asctime)s [%(filename)s] [%(levelname)s] %(message)s', level=log_level, datefmt='%Y-%m-%d %H:%M:%S', filename=logfile)
logging.info('=== START OF SESSION ===')

# Verbose
verbose = False
if(len(sys.argv) > 1):
    if(sys.argv[1] == '-v'):
        verbose = True

# Query API
try:
    response = urllib.urlopen(base + "forecast10day" + city )
    data_json = json.loads(response.read())
except:
    logging.error('No data received from Weather Underground')
    sys.exit()

# Get 10 day forecast
today_high_temp = int(data_json['forecast']['simpleforecast']['forecastday'][0]['high']['celsius'])
if(verbose):
    print "Todays maximum temperature is: %dC" % (today_high_temp)
for d in range(0, 10):
    qpf_allday.append(int(data_json['forecast']['simpleforecast']['forecastday'][d]['qpf_allday']['mm']))
    qpf_allweek += qpf_allday[d]
if(verbose):
    print "This weeks rain forecast per day is:"
    print qpf_allday
    print "This weeks rain forecast in total is: %d" % (qpf_allweek)

# Process forecast to sprinkler mode
if (today_high_temp > lim_high_temp):
    if (qpf_allday[0] < lim_qpf_allday):
        # Very hot and no rain today so high sprinkler mode
        sprinkler_duration = high_duration
        sprinkler_times = high_times
        sprinkler_mode = 'high'
elif (today_high_temp > lim_med_temp):
    if (qpf_allday[0] < lim_qpf_allday):
        # Hot and no rain today so medium sprinkler mode
        sprinkler_duration = med_duration
        sprinkler_times = med_times
        sprinkler_mode = 'medium'
elif (today_high_temp > lim_low_temp):
    if (qpf_allweek[0] < lim_qpf_allweek):
        # Warm and no rain this week so low sprinkler mode
        sprinkler_duration = low_duration
        sprinkler_times = low_times
        sprinkler_mode = 'low'
if(verbose):
    print "Sprinkler mode for today is: %s" % (sprinkler_mode)

# Control actuators
hour = dt.datetime.now().hour
if (hour in sprinkler_times):
    try:
        f = urllib.urlopen(sprinkler_on)
        logging.info("Sprinklers enabled for %d minutes [%s mode]" % (sprinkler_duration, sprinkler_mode))
        sleep(sprinkler_duration*60)
        f = urllib.urlopen(sprinkler_off)
        logging.info("Sprinklers disabled after %d minutes [%s mode]" % (sprinkler_duration, sprinkler_mode))
    except:
        logging.error('No data received from Weather Underground')
        sys.exit()
else:
    logging.info("No action required [%s mode]" % (sprinkler_mode))

# End program
logging.info('=== END OF SESSION ===')
