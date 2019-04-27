# Public packages
import os
import datetime as dt
import sys
from time import sleep
import pickle
import yaml

# Private packages
import arduino
import nebula
import openweathermap

ON = 0
OFF = 1

# Load configuration YAML
path = os.path.dirname(os.path.realpath(__file__))
fp = open(path + '/config.yaml', 'r')
cfg = yaml.load(fp)

# Set up Nebula API client
nebula_client = nebula.Client(**cfg['nebula'])

# Set up Guard House Arduino client
arduino_client = arduino.Client(**cfg['guardhouse'])

# Set up OpenWeatherMap
owm_client = openweathermap.Client(**cfg['WU'])

# Settings
# Limits
lim_high_temp = 35                  # C
lim_med_temp = 30                   # C
lim_low_temp = 25                   # C
lim_days_ahead_high_temp = 1        # days
lim_days_ahead_med_temp = 2         # days
lim_days_ahead_low_temp = 3         # days
lim_rain_ahead_high_temp = 5         # mm
lim_rain_ahead_med_temp = 3          # mm
lim_rain_ahead_low_temp = 3          # mm
lim_rain_yesterday_high_temp = 4     # mm
lim_rain_yesterday_med_temp = 2      # mm
lim_rain_yesterday_low_temp = 1      # mm

# Sprinkler modes
high_duration = 5                   # mins
med_duration = 5                    # mins
low_duration = 3                    # mins
high_times = [8, 13, 18]
med_times = [8, 18]
low_times = [18]

# Check command line parameters
verbose = False
force = False
if len(sys.argv) > 1:
    if 'v' in sys.argv[1]:
        verbose = True
    if 'f' in sys.argv[1]:
        force = True

# Intialize
hour = dt.datetime.now().hour
path = os.path.dirname(os.path.realpath(__file__))

# Run forecast once a day at 6 o'clock or forced
if hour == 6 or force:
    # Define variables
    qpf_days_ahead = 0
    lim_days_ahead = 0
    sprinkler_times = []
    sprinkler_duration = 0
    sprinkler_mode = 'off'

    # Query API

    # Write forecast to file
    if not owm_client.forecast():
        with open(path + '/sprinkler.pickle', 'wb') as fp:
            # Write 'safe' values to pickle file (no sprinkling)
            pickle.dump([0, 'off', 0, []], fp)
        sys.exit()

    # Get yesterdays precipitation from file
    try:
        with open(path + '/sprinkler.pickle', 'rb') as fp:
            pickle_load = pickle.load(fp)
            rain_yesterday = pickle_load[0]
    except FileNotFoundError:
        nebula_client.error('Sprinkler.pickle file not found')
        # Write forecast to file
        with open(path + '/sprinkler.pickle', 'wb') as fp:
            # Write 'safe' values to pickle file (no sprinkling)
            pickle.dump([0, 'off', 0, []], fp)
        sys.exit()

    # Get 10 day forecast
    # Temperature
    if verbose:
        print('Todays maximum temperature is: %dC' % owm_client.temp[0])
        print('Yesterday recorded rain: %s mm' % rain_yesterday)
        print('Next 3 days rain forecast per day is: %s mm' % owm_client.rain)

    # Process forecast to sprinkler mode
    if owm_client.temp[0] > lim_high_temp:
        if rain_yesterday < lim_rain_yesterday_high_temp:
            qpf_days_ahead = sum(owm_client.rain[0:lim_days_ahead_high_temp])
            lim_days_ahead = lim_days_ahead_high_temp
            if qpf_days_ahead < lim_rain_ahead_high_temp:
                # Very hot and no rain today so high sprinkler mode
                sprinkler_duration = high_duration
                sprinkler_times = high_times
                sprinkler_mode = 'high'
    elif owm_client.temp[0]  > lim_med_temp:
        if rain_yesterday < lim_rain_yesterday_med_temp:
            qpf_days_ahead = sum(owm_client.rain[0:lim_days_ahead_med_temp])
            lim_days_ahead = lim_days_ahead_med_temp
            if qpf_days_ahead < lim_rain_ahead_med_temp:
                # Hot and no rain today so medium sprinkler mode
                sprinkler_duration = med_duration
                sprinkler_times = med_times
                sprinkler_mode = 'medium'
    elif owm_client.temp[0]  > lim_low_temp:
        if rain_yesterday < lim_rain_yesterday_low_temp:
            qpf_days_ahead = sum(owm_client.rain[0:lim_days_ahead_low_temp])
            lim_days_ahead = lim_days_ahead_low_temp
            if qpf_days_ahead < lim_rain_ahead_low_temp:
                # Warm and no rain next x days so low sprinkler mode
                sprinkler_duration = low_duration
                sprinkler_times = low_times
                sprinkler_mode = 'low'

    if verbose:
        if lim_days_ahead:
            print('Next %d days rain forecast in total is: [%s] mm' %
                  (lim_days_ahead, sum(owm_client.rain[0:lim_days_ahead])))
        print('Sprinkler mode for today is: %s' % sprinkler_mode)

    # Write daily forecast summary to logging
    nebula_client.info("= DAILY WEATHER FORECAST =")
    nebula_client.info("Forecasted maximum temperature is: %dC" % owm_client.temp[0])
    nebula_client.info("Yesterday recorded rain: %s mm" % rain_yesterday)
    nebula_client.info("Next 3 days rain forecast per day is: %s mm" % owm_client.rain)
    if lim_days_ahead:
        nebula_client.info("Next %d days rain forecast in total is: %s mm" %
                           (lim_days_ahead, sum(owm_client.rain[0:lim_days_ahead])))
    nebula_client.info("Sprinkler mode for today is: %s" % sprinkler_mode)

    # Write forecast to file
    with open(path + '/sprinkler.pickle', 'wb') as fp:
        pickle.dump([owm_client.rain[0], sprinkler_mode, sprinkler_duration, sprinkler_times], fp)

try:
    with open(path + '/sprinkler.pickle', 'rb') as fp:
        rain_yesterday, sprinkler_mode, sprinkler_duration, sprinkler_times = pickle.load(fp)
except FileNotFoundError:
    # No forecast found
    sprinkler_times = []

if hour in sprinkler_times:
    if arduino_client.set_value('water_mode', ON):
        nebula_client.info("Sprinklers enabled for %d minutes [%s mode]" % (sprinkler_duration, sprinkler_mode))
    else:
        nebula_client.warning('Unable to activate sprinklers')
    sleep(sprinkler_duration*60)
    if arduino_client.set_value('water_mode', OFF):
        nebula_client.info("Sprinklers disabled after %d minutes [%s mode]" % (sprinkler_duration, sprinkler_mode))
    else:
        nebula_client.critical('Unable to de-activate sprinklers!')

