import schedule
import requests
import logger
from phue import Bridge
import yaml
import time
import random

# Scheduler reference examples
#  schedule.every(5).to(10).days.do(job)
#  schedule.every().monday.do(job)
#  schedule.every().wednesday.at("13:15").do(job)
#  schedule.every(10).seconds.do(job)
#  schedule.every().hour.do(job)

# Set up logger
log_client = logger.Client('scheduler', 'info')

# Load configuration YAML
fp = open('config.yaml','r')
cfg = yaml.load(fp)


# Define jobs
def reset_rain_meter():
    r = requests.get('http://192.168.1.112/rain/0')
    log_client.info('Rain meter reset to 0')


def lights_on():
    # Connect to Hue Bridge
    b = Bridge(cfg['hue']['url'])
    # Get current light state
    hueLights = b.lights
    hueGroups = b.groups
    hueScenes = b.scenes

    # Check if all lights off
    all_off = True
    for light in hueLights:
        if not light.on:
            all_off = False
    if all_off:
        b.activate_scene(hueGroups[0].group_id, get_scene_by_name('Away', hueScenes))


def lights_out():
    # Connect to Hue Bridge
    b = Bridge(cfg['hue']['url'])
    # Get current light state
    hueLights = b.lights
    hueGroups = b.groups
    # Check if 'away' scene active
    if not get_active_scene('away', hueLights):
        # Turn all lights off within a set random time
        time.sleep(random.randint(1,cfg['hue']['random']))
        log_client.info('Lights out!')
        hueGroups[0].on = False


def get_active_scene(name, lights):
    for id in cfg['hue']['scenes'][name]['lights']:
        if cfg['hue']['scenes'][name]['lights'][id]['state']:
            # Light should be on, verify that it is
            if (lights[id].on):
                # Light is on, verify xy brightness and color (xy)
                if not cfg['hue']['scenes'][name]['lights'][id]['brightness'] == lights[id].brightness or \
                        not cfg['hue']['scenes'][name]['lights'][id]['xy'] == lights[id].xy:
                    return False
            else:
                return False
        else:
            # Light should be off, verify that it is
            if lights[id].on:
                return False
    return True


def get_scene_by_name(name, scenes):
    for scene in scenes:
        if scene.name == name:
            return scene.scene_id
    return 0


# Schedule jobs
schedule.every().day.at("00:00").do(reset_rain_meter)
schedule.every().day.at("22:30").do(lights_out)
schedule.every().day.at("18:00").do(lights_on)

# Run scheduler
log_client.info('Scheduler started')
while True:
    schedule.run_pending()
    time.sleep(1)
