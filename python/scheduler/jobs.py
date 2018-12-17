import random
import yaml
import time
import arduino
import hue

# Load configuration YAML
fp = open('config.yaml','r')
cfg = yaml.load(fp)

# Set up Guard House Arduino client
arduino_client = arduino.Client(cfg['guardhouse']['url'])

# Set up Hue client
hue_client = hue.Client(cfg['hue']['ip'])


# Define jobs
def reset_rain_meter(log_client):
    if arduino_client.set_value('rain',0):
        log_client.info('Rain meter reset to 0')


def lights_out(log_client):
    if hue_client.get_scene(cfg['hue']['scenes']['not home']):
        # Turn all lights off within a set random time
        delay = random.randint(1,cfg['hue']['random'])
        log_client.info('Switching lights off in %d seconds!' % delay)
        time.sleep(delay)
        hue_client.set_all_off()