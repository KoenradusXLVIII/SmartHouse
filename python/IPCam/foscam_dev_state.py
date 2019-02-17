# Run with logging: python3 foscam_dev_state.py >> foscam_dev_state.py.log 2>&1 &

# Public pacakages
import requests
import re
import yaml
import time
import signal
import sys
from xml.etree import ElementTree

# Personal
import nebula
import pushover
import arduino
import hue

# Load configuration YAML
fp = open('config.yaml', 'r')
cfg = yaml.load(fp)

# Set up Pushover client
pushover_client = pushover.Client(**cfg['pushover'])

# Set up Nebula API client
nebula_client = nebula.Client(**cfg['nebula'])
nebula_client.set_level(nebula.DEBUG)

# Set up Guard House Arduino client
arduino_client = arduino.Client(**cfg['guardhouse'])

# Set up Hue client
hue_client = hue.Client(**cfg['hue'])


def main():
    # Initialize variables
    last_motion_state = cfg['foscam']['state']['no alarm']
    last_infra_led_state = 0
    motor_light_state = 0
    motion_timer = 0
    time_out = cfg['foscam']['interval']['poll'];


    nebula_client.info('Foscam and Pushover monitoring scripts activated')
    while True:
        # Sleep for 5 seconds
        time.sleep(time_out)

        # Get Foscam device state
        foscam_dev_state = devstate()

        if foscam_dev_state:
            # Reset time out to default
            if time_out == cfg['foscam']['interval']['time-out']:
                time_out = cfg['foscam']['interval']['poll']
                nebula_client.info('Time-out reset to default polling interval: %d seconds' % time_out)
            # Check to see if infrared LEDs on (detect day/night transition)
            infra_led_state = int(foscam_dev_state.find('infraLedState').text)
            if infra_led_state != last_infra_led_state:
                # Update Guard House API
                if arduino_client.set_value('day_night', infra_led_state):
                    if infra_led_state:  # night
                        nebula_client.info('Transition to night written to Guard House API')
                        # If no one home turns lights on in 'not home' mode
                        if hue_client.get_all_off():
                            hue_client.set_scene('Not home')
                            nebula_client.info('Switching lights on to \'Not home\' mode')
                    else:  # day
                        nebula_client.info('Transition to day written to Guard House API')
                else:
                    nebula_client.warning('Failed to write \'day_night\' to Guard House API')

            last_infra_led_state = infra_led_state

            # Check for motion detection
            motion_detect = foscam_dev_state.find('motionDetectAlarm').text
            if (last_motion_state == cfg['foscam']['state']['no alarm']) and (
                    motion_detect == cfg['foscam']['state']['alarm']):
                # Log to Nebula
                nebula_client.warning('Motion alert!')

                if (time.time() - motion_timer) > cfg['motor']['hysteresis']:
                    nebula_client.debug('New motion detected outside hysteresis interval, starting counter')
                    # Alarm handling
                    if arduino_client.get_value('alarm_mode'):
                        pushover_client.message('Alarm triggered!', snapshot(), 'GuardHouse Security', 'high', 'alien')

                    # Light handling
                    if arduino_client.get_value('day_night'):
                        # It is dark out so we should turn the light on if...
                        if not motor_light_state:
                            # ... it is off
                            motor_light_state = 1
                            if arduino_client.set_value('motor_light', motor_light_state):
                                nebula_client.debug('Wrote \'HIGH\' to \'motor_light\' to the Guard House API')
                            else:
                                nebula_client.warning('Failed to write \'motor_light\' to the Guard House API')
                else:
                    nebula_client.debug('Motion detected within hysteresis interval, resetting counter')

                motion_timer = time.time()
            else:
                # Light handling
                if (time.time() - motion_timer) > cfg['motor']['hysteresis']:
                    # Last change to light setting was more then the hysteresis limit, so a change is allowed
                    if motor_light_state:
                        # There is no motion detected and the light is on so we turn the light off
                        motor_light_state = 0
                        if arduino_client.set_value('motor_light', motor_light_state):
                            nebula_client.debug('Wrote \'LOW\' to \'motor_light\' to the Guard House API')
                        else:
                            nebula_client.warning('Failed to write \'motor_light\' to the Guard House API')

            last_motion_state = motion_detect
        else:
            time_out = cfg['foscam']['interval']['time-out'];
            nebula_client.info('Time-out interval changed to: %d seconds' % time_out)
            cfg['foscam']['motor']['url'] = 'http://192.168.1.81:88/'

def devstate():
    # Read device status
    try:
        cgi_url = cfg['foscam']['motor']['url'] + cfg['foscam']['motor']['cgi']
        payload = {'usr': cfg['foscam']['motor']['user'], 'pwd': cfg['foscam']['motor']['pass'], 'cmd': 'getDevState'}
        r = requests.get(cgi_url, params=payload, timeout=1)
        return ElementTree.fromstring(r.text)  # Extract XML tree
    except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout):
        nebula_client.warning('Unable to read device status [invalid response from Foscam API]')
        return None


def snapshot():
    # Capture snapshot
    try:
        cgi_url = cfg['foscam']['motor']['url'] + cfg['foscam']['motor']['cgi']
        payload = {'usr': cfg['foscam']['motor']['user'], 'pwd': cfg['foscam']['motor']['pass'], 'cmd': 'snapPicture'}
        r = requests.get(cgi_url, params=payload)
        reg = re.search(r'(Snap_\d{8}-\d{6}.jpg)', r.text)  # Get snapshot name: Snap_YYYYMMDD_HHMMSS.jpg
        snap_url = cfg['foscam']['motor']['url'] + 'snapPic/' + reg.group(1)
        r = requests.get(snap_url)
        return r.content
    except ConnectionError:
        nebula_client.warning('Unable to capture snapshot [invalid response from Foscam API]')
        return None


def exit_gracefully(sig, frame):
    nebula_client.info('Foscam and Pushover monitoring scripts de-activated.')
    sys.exit()


# Attach signals to catch SIGINT (CTRL-c) and SIGTERM (kill)
signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)
if __name__ == "__main__":
    print('Foscam and Pushover monitoring scripts activated')
    main()
