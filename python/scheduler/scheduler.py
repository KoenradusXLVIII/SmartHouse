# Public packages
import schedule
import random
import yaml
import time
import datetime
import traceback

# Local packages
import arduino
import hue
import nebula


# Load configuration YAML
fp = open('config.yaml','r')
cfg = yaml.load(fp)

# Set up Guard House Arduino client
arduino_client = arduino.Client(**cfg['guardhouse'])

# Set up Hue client
hue_client = hue.Client(cfg['hue']['ip'])

# Set up Nebula API client
nebula_client = nebula.Client(**cfg['nebula'])


'''
 DEFINE JOBS
'''


def reset_rain_meter():
    if arduino_client.set_value('rain', 0):
        nebula_client.info('Rain meter reset to 0')
    else:
        nebula_client.warning('Unable to reset rain meter!')


def lights_out():
    if hue_client.get_scene(cfg['hue']['scenes']['not home']):
        # Turn all lights off within a set random time
        delay = random.randint(1, cfg['hue']['random'])
        nebula_client.info('Switching lights off in %d seconds!' % delay)
        time.sleep(delay)
        hue_client.set_all_off()
        nebula_client.info('Lights off!')


'''
 SCHEDULE JOBS
 
 Scheduler reference examples
 - schedule.every(5).to(10).days.do(job)
 - schedule.every().monday.do(job)
 - schedule.every().wednesday.at("13:15").do(job)
 - schedule.every(10).seconds.do(job)
 - schedule.every().hour.do(job)
'''

schedule.every().day.at("00:00").do(reset_rain_meter)
schedule.every().day.at("22:30").do(lights_out)

# Run scheduler
while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except:
        with open("exceptions.log", "a") as log:
            log.write("%s: Exception occurred:\n" % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            traceback.print_exc(file=log)


