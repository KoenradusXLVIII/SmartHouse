import requests
import re
import yaml
import time
import platform
import logging.handlers
from pushover import client
from xml.etree import ElementTree as ET
from io import BytesIO

# Identify platform
print('Running code on: {}'.format(platform.system()))

# Load configuration YAML
fp = open('config.yaml','r')
cfg = yaml.load(fp)

# Set up Pushover
pushover = client(cfg['pushover']['token'], cfg['pushover']['user'], cfg['pushover']['url'])

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

def main():
    # Initialize variables
    lastMotionState = cfg['foscam']['state']['no alarm']
    logger.info('Foscam and Pushover monitoring scripts activated.')

    while True:
        # Sleep for 5 seconds
        time.sleep(5)

        # Check for motion alarm
        motionDetectAlarm = devstate()
        if motionDetectAlarm:
            if (lastMotionState == cfg['foscam']['state']['no alarm']) and (motionDetectAlarm == cfg['foscam']['state']['alarm']):
                logger.warning('Alarm triggered!')
                snap = snapshot()
                if snap:
                    pushover.message('Alarm triggered!', snapshot(), 'GuardHouse Security', 'high', 'alien')
                else:
                    pushover.message('Alarm triggered, but unable to capture snapshot', '', 'GuardHouse Security', 'high', 'alien')
            lastMotionState = motionDetectAlarm

    logger.error('Foscam and Pushover monitoring scripts de-activated.')

def devstate():
    # Read device status
    try:
        cgi_url = cfg['foscam']['motor']['url'] + cfg['foscam']['motor']['cgi']
        payload = {'usr': cfg['foscam']['motor']['user'], 'pwd': cfg['foscam']['motor']['pass'], 'cmd': 'getDevState'}
        r = requests.get(cgi_url, params=payload)
        root = ET.fromstring(r.text)    # Extract XML tree
        return root.find('motionDetectAlarm').text
    except:
        logger.warning('Unable to read device status [invalid response from Foscam API]')
        return None

def snapshot():
    # Capture snapshot
    try:
        cgi_url = cfg['foscam']['motor']['url'] + cfg['foscam']['motor']['cgi']
        payload = {'usr': cfg['foscam']['motor']['user'], 'pwd': cfg['foscam']['motor']['pass'], 'cmd': 'snapPicture'}
        r = requests.get(cgi_url, params=payload)
        reg = re.search('(Snap_\d{8}-\d{6}.jpg)',r.text)    # Get snapshot name: Snap_YYYYMMDD_HHMMSS.jpg
        snap_url = cfg['foscam']['motor']['url'] + 'snapPic/' + reg.group(1)
        r = requests.get(snap_url)
        return r.content
    except:
        logger.warning('Unable to capture snapshot [invalid response from Foscam API]')
        return None

if __name__ == "__main__":
    main()
