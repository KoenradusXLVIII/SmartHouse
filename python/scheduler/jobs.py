import requests
from phue import Bridge
import random
import yaml
import time
import arduino
from helpers import get_active_scene, get_scene_by_name

# Load configuration YAML
fp = open('config.yaml','r')
cfg = yaml.load(fp)

# Set up Guard House Arduino client
arduino_client = arduino.Client(cfg['guardhouse']['url'])


# Define jobs
def reset_rain_meter(log_client):
    r = requests.get('http://192.168.1.112/rain/0')
    log_client.info('Rain meter reset to 0')


def check_lights_on(log_client):
    # Check to see if it is dark outside
    if arduino_client.get_value('day_night'):
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
            log_client.info('Lights on')
            b.activate_scene(hueGroups[0].group_id, get_scene_by_name('Not home', hueScenes))


def lights_out(log_client):
    # Connect to Hue Bridge
    b = Bridge(cfg['hue']['url'])
    # Get current light state
    hueLights = b.lights
    hueGroups = b.groups
    # Check if 'Not home' scene active
    if get_active_scene('Not home', hueLights, cfg):
        # Turn all lights off within a set random time
        delay = random.randint(1,cfg['hue']['random'])
        log_client.info('Lights out in %d seconds!' % delay)
        time.sleep(delay)
        hueGroups[0].on = False