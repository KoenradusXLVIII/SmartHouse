import requests
import os
import yaml
import time
import platform
import logging.handlers
from xml.etree import ElementTree as ET

# Identify platform
print('Running code on: {}'.format(platform.system()))

# Set up logging
log_level = logging.INFO
formatter = logging.Formatter('%(name)s [%(levelname)s] %(message)s')
# Set up handler (Linux only)
if platform.system() == 'Linux':
    handler = logging.handlers.SysLogHandler(address = '/dev/log')
    handler.setLevel(log_level)
    handler.setFormatter(formatter)
# Create logging instance
logger = logging.getLogger('foscam')
logger.setLevel(log_level)
# Add handler (Linux only)
if platform.system() == 'Linux':
    logger.addHandler(handler)

# Load configuration YAML
path = os.path.dirname(os.path.realpath(__file__))
cfg = yaml.load(open(path + '/config.yaml','r'))

# Initialize variables
lastMotionState = cfg['foscam']['state']['no alarm']

while True:
    # Sleep for 5 seconds
    time.sleep(5)

    # Read device status
    try:
        fp = requests.get(cfg['foscam']['motor'])
    except:
        logger.warning('Not able to reach Foscam API')
        continue

    try:
        root = ET.fromstring(fp.text) # Extract XML tree
        motionDetectAlarm = root.find('motionDetectAlarm').text
        if (lastMotionState == cfg['foscam']['state']['no alarm']) and (motionDetectAlarm == cfg['foscam']['state']['alarm']):
            print('Alarm triggerred!')
            logger.warning('Alarm triggered!')
        lastMotionState = motionDetectAlarm
    except:
        logger.warning('Invalid data received from Foscam API')
        continue