import requests
import re
import yaml
import time
import platform
import logging.handlers
from pushover import Pushover
from logger import Logger
from xml.etree import ElementTree as ET
from io import BytesIO

# Identify platform
print('Running code on: {}'.format(platform.system()))

# Load configuration YAML
fp = open('config.yaml','r')
cfg = yaml.load(fp)

# Set up Pushover
pushover = Pushover(cfg['pushover']['token'], cfg['pushover']['user'])

# Set up logger
log_client = Logger('foscam', 'info')

def main():
    # Initialize variables
    lastMotionState = cfg['foscam']['state']['no alarm']
    log_client.info('Foscam and Pushover monitoring scripts activated.')

    while True:
        # Sleep for 5 seconds
        time.sleep(5)

        # Check for motion alarm
        motionDetectAlarm = devstate()
        if motionDetectAlarm:
            if (lastMotionState == cfg['foscam']['state']['no alarm']) and (motionDetectAlarm == cfg['foscam']['state']['alarm']):
                log_client.warning('Alarm triggered!')
                snap = snapshot()
                if snap:
                    pushover.message('Alarm triggered!', snapshot(), 'GuardHouse Security', 'high', 'alien')
                else:
                    pushover.message('Alarm triggered, but unable to capture snapshot', '', 'GuardHouse Security', 'high', 'alien')
            lastMotionState = motionDetectAlarm

    log_client.error('Foscam and Pushover monitoring scripts de-activated.')

def devstate():
    # Read device status
    try:
        cgi_url = cfg['foscam']['motor']['url'] + cfg['foscam']['motor']['cgi']
        payload = {'usr': cfg['foscam']['motor']['user'], 'pwd': cfg['foscam']['motor']['pass'], 'cmd': 'getDevState'}
        r = requests.get(cgi_url, params=payload)
        root = ET.fromstring(r.text)    # Extract XML tree
        return root.find('motionDetectAlarm').text
    except:
        log_client.warning('Unable to read device status [invalid response from Foscam API]')
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
        log_client.warning('Unable to capture snapshot [invalid response from Foscam API]')
        return None

if __name__ == "__main__":
    main()
