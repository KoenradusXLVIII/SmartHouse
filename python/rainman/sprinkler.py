# Public packages
import sys
from time import sleep
import yaml
import os

# Private packages
import arduino
import nebula

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


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


if len(sys.argv) > 1:
    if 'off' in sys.argv[1]:
        if arduino_client.set_value('water_mode', OFF):
            nebula_client.info('Sprinklers manually disabled')
        else:
            nebula_client.critical('Unable to de-activate sprinklers!')
    elif 'on' in sys.argv[1]:
        if is_int(sys.argv[2]):
            sprinkler_duration = int(sys.argv[2])
            if arduino_client.set_value('water_mode', ON):
                nebula_client.info('Sprinklers enabled for %d minutes' % sprinkler_duration)
            else:
                nebula_client.warning('Unable to activate sprinklers')
            sleep(sprinkler_duration * 60)
            if arduino_client.set_value('water_mode', OFF):
                nebula_client.info(
                    'Sprinklers disabled after %d minutes' % sprinkler_duration)
            else:
                nebula_client.critical('Unable to de-activate sprinklers!')
    else:
        nebula_client.critical('Invalid sprinkler arguments supplied')
else:
    nebula_client.warning('No sprinkler arguments supplied')
