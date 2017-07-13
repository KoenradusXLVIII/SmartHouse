import urllib
import json
import datetime as dt
import sys
from time import sleep
import pickle
import logging

# Weather Underground API
base = "http://api.wunderground.com/api/f0c3002dabae8c04/"
city = "/q/NL/Eindhoven.json"

# SmartHouse API
sprinkler_on = "http://192.168.1.112/water_mode/manual"
sprinkler_off = "http://192.168.1.112/water_mode/auto"

# Set up logging
base_path = '/media/usb/log/'
logfile = base_path + 'output.log'
log_level = logging.INFO
logging.basicConfig(format='%(asctime)s [%(filename)s] [%(levelname)s] %(message)s', level=log_level, datefmt='%Y-%m-%d %H:%M:%S', filename=logfile)

# Settings
# Limits
lim_high_temp = 30 # C
lim_med_temp = 25 # C
lim_low_temp = 20 # C
lim_days_ahead_high_temp = 1 # days
lim_days_ahead_med_temp = 1 # days
lim_days_ahead_low_temp = 3 # days
lim_qpf_ahead_high_temp = 5 # mm
lim_qpf_ahead_med_temp = 3 # mm
lim_qpf_ahead_low_temp = 3 # mm
lim_qpf_yesterday_high_temp = 8 # mm
lim_qpf_yesterday_med_temp = 4 # mm
lim_qpf_yesterday_low_temp = 2 # mm

# Sprinkler modes
high_duration = 10 # mins
med_duration = 10 # mins
low_duration = 10 # mins
high_times = [8, 11, 14, 17, 20]
med_times = [8, 13, 18]
low_times = [8, 18]

# Verbose
verbose = False
if(len(sys.argv) > 1):
    if('v' in sys.argv[1]):
        verbose = True

# Intialize
hour = dt.datetime.now().hour

# Run forecast once a day at 6 o'clock or forced
if (hour == 6) or ('f' in sys.argv[1]):
# Define variables
    qpf_allday = []
    qpf_days_ahead = 0
    lim_days_ahead = 0
    sprinkler_times = []
    sprinkler_duration = 0
    sprinkler_mode = 'off'

    # Query API
    try:
        response = urllib.urlopen(base + "forecast10day" + city )
        data_json = json.loads(response.read())
    except:
        logging.error('No data received from Weather Underground')
        sys.exit()

    # Get yesterdays precipitation from file
    with open('sprinkler.pickle') as fp:
        qpf_yesterday = pickle.load(fp)

    # Get 10 day forecast
    # Temperature
    today_high_temp = int(data_json['forecast']['simpleforecast']['forecastday'][0]['high']['celsius'])
    if(verbose):
        print "Todays maximum temperature is: %dC" % (today_high_temp)
    # Quantitative Precipitation Forecast
    for d in range(0, 10):
        qpf_allday.append(int(data_json['forecast']['simpleforecast']['forecastday'][d]['qpf_allday']['mm']))
    # Store todays precipitation for tomorrow
    qpf_yesterday = qpf_allday[0]

    if(verbose):
        print "Yesterday recorded rain: %s mm" % (qpf_yesterday)
        print "Next 10 days rain forecast per day is: [%s] mm" % (str(qpf_allday)[1:-1])

    # Process forecast to sprinkler mode
    if (today_high_temp > lim_high_temp):
        if (qpf_yesterday < lim_qpf_yesterday_high_temp):
            qpf_days_ahead = sum(qpf_allday[0:lim_days_ahead_high_temp])
            lim_days_ahead = lim_days_ahead_high_temp
            if (qpf_days_ahead < lim_qpf_ahead_high_temp):
                # Very hot and no rain today so high sprinkler mode
                sprinkler_duration = high_duration
                sprinkler_times = high_times
                sprinkler_mode = 'high'
    elif (today_high_temp > lim_med_temp):
        if (qpf_yesterday < lim_qpf_yesterday_med_temp):
            qpf_days_ahead = sum(qpf_allday[0:lim_days_ahead_med_temp])
            lim_days_ahead = lim_days_ahead_med_temp
            if (qpf_days_ahead < lim_qpf_ahead_med_temp):
                # Hot and no rain today so medium sprinkler mode
                sprinkler_duration = med_duration
                sprinkler_times = med_times
                sprinkler_mode = 'medium'
    elif (today_high_temp > lim_low_temp):
        if (qpf_yesterday < lim_qpf_yesterday_low_temp):
            qpf_days_ahead = sum(qpf_allday[0:lim_days_ahead_low_temp])
            lim_days_ahead = lim_days_ahead_low_temp
            if (qpf_days_ahead < lim_qpf_ahead_low_temp):
                # Warm and no rain next x days so low sprinkler mode
                sprinkler_duration = low_duration
                sprinkler_times = low_times
                sprinkler_mode = 'low'

    if(verbose):
        if(lim_days_ahead):
            print "Next %d days rain forecast in total is: [%s] mm" % (lim_days_ahead, str(qpf_allday)[1:3*lim_days_ahead-1])
        print "Sprinkler mode for today is: %s" % (sprinkler_mode)

    # Write daily forecast summary to logging
    logging.info("= DAILY WEATHER FORECAST =")
    logging.info("Forecasted maximum temperature is: %dC" % (today_high_temp))
    logging.info("Next 10 days rain forecast per day is: [%s] mm" % (str(qpf_allday)[1:-1]))
    if(lim_days_ahead):
        logging.info("Next %d days rain forecast in total is: [%s] mm" % (lim_days_ahead, str(qpf_allday)[1:3*lim_days_ahead-1]))
    logging.info("Sprinkler mode for today is: %s" % (sprinkler_mode))
    with open('sprinkler.pickle', 'w') as fp:
        pickle.dump([today_high_temp,qpf_allday,qpf_yesterday,lim_days_ahead,sprinkler_mode,sprinkler_duration,sprinkler_times], fp)

with open('sprinkler.pickle') as fp:
    today_high_temp, qpf_allday,qpf_yesterday,lim_days_ahead,sprinkler_mode,sprinkler_duration,sprinkler_times = pickle.load(fp)

if (hour in sprinkler_times):
    try:
        logging.info("Latest maximum temperature forecast is: %dC" % (today_high_temp))
        if(lim_days_ahead):
            logging.info("Latest %d days rain forecast in total is: [%s] mm" % (lim_days_ahead, str(qpf_allday)[1:3*lim_days_ahead-1]))
        logging.info("Sprinkler mode is: %s" % (sprinkler_mode))
        f = urllib.urlopen(sprinkler_on)
        logging.info("Sprinklers enabled for %d minutes [%s mode]" % (sprinkler_duration, sprinkler_mode))
        sleep(sprinkler_duration*60)
        f = urllib.urlopen(sprinkler_off)
        logging.info("Sprinklers disabled after %d minutes [%s mode]" % (sprinkler_duration, sprinkler_mode))
    except:
        logging.error('Unable to connect to GuardHouse')
        sys.exit()
