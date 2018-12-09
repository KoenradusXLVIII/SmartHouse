import requests
import re
import yaml
import time
import pushover
import logger
import arduino
import signal
import sys
from xml.etree import ElementTree as ET

# Load configuration YAML
fp = open('config.yaml','r')
cfg = yaml.load(fp)

# Set up Pushover client
pushover_client = pushover.Client(cfg['pushover']['token'], cfg['pushover']['user'])

# Set up logger client
log_client = logger.Client('foscam', log_level='info', pushover_client=pushover_client)

# Set up Guard House Arduino client
arduino_client = arduino.Client(cfg['guardhouse']['url'])


def main():
    # Initialize variables
    last_motion_state = cfg['foscam']['state']['no alarm']
    last_infra_led_state = 0
    light_timer = 0
    log_client.info('Foscam and Pushover monitoring scripts activated.')

    while True:
        # Sleep for 5 seconds
        time.sleep(5)

        # Get Foscam device state
        foscam_dev_state = devstate()

        # Check to see if infrared LEDs on (detect day/night transition)
        infra_led_state = foscam_dev_state.find('infraLedState').text
        if infra_led_state != last_infra_led_state:
            if not arduino_client.set_value('day_night',infra_led_state):
                log_client.warning('Failed to write \'day_night\' to Guard House API')

        # Check for motion detection
        motion_detect = foscam_dev_state.find('motionDetectAlarm').text
        if motion_detect:
            # Alarm handling
            if (last_motion_state == cfg['foscam']['state']['no alarm']) and (motion_detect == cfg['foscam']['state']['alarm']):
                #log_client.warning('Alarm triggered!')
                pushover_client.message('Alarm triggered!', snapshot(), 'GuardHouse Security', 'high', 'alien')
            last_motion_state = motion_detect

            # Light handling
            if (time.time() - light_timer) > cfg['motor']['hysteresis']:
                # Last change to light setting was more then the hysteresis limit, so a change is allowed
                if arduino_client.get_value('day_night'):
                    # It is dark out so we should turn the light on
                    if not arduino_client.get_value('motor_light'):
                        # Turn light on if it is off
                        if not arduino_client.set_value('motor_light', 1):
                            log_client.warning('Failed to write \'motor_light\' to the Guard House API')
                        # Set the hysteresis timer
                        light_timer = time.time()
        else:
            # Light handling
            if (time.time() - light_timer) > cfg['motor']['hysteresis']:
                # Last change to light setting was more then the hysteresis limit, so a change is allowed
                # There is no motion detected so we turn the light off
                if not arduino_client.set_value('motor_light', 0):
                    log_client.warning('Failed to write \'motor_light\' to the Guard House API')


def devstate():
    # Read device status
    try:
        cgi_url = cfg['foscam']['motor']['url'] + cfg['foscam']['motor']['cgi']
        payload = {'usr': cfg['foscam']['motor']['user'], 'pwd': cfg['foscam']['motor']['pass'], 'cmd': 'getDevState'}
        r = requests.get(cgi_url, params=payload)
        return ET.fromstring(r.text)    # Extract XML tree
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


def exit_gracefully(sig, frame):
    log_client.info('Foscam and Pushover monitoring scripts de-activated.')
    sys.exit()


# Attach signals to catch SIGINT (CTRL-c) and SIGTERM (kill)
signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)
if __name__ == "__main__":
    main()
