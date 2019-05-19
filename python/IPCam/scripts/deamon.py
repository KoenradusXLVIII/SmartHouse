# Public pacakages
import yaml
import os
import time
import sys
import platform
import psutil

# Private packages
import IPCam
import pushover
import arduino
import nebula
import hue

# Load configuration YAML
path = os.path.dirname(os.path.realpath(__file__))
fp = open(path + '/config.yaml', 'r')
cfg = yaml.load(fp)

# Set up Nebula API client
nebula_client = nebula.Client(**cfg['nebula'])
nebula_client.set_level(nebula.INFO)

# Start deamon
# PID file location
if platform.system() == 'Windows':
    pidfile = 'c:\\tmp\\IPCam_daemon.pid'
elif platform.system() == 'Linux':
    pidfile = '/tmp/IPCam_daemon.pid'

# Check if deamon already running
if os.path.isfile(pidfile):
    with open(pidfile, 'r') as fp:
        pid = int(fp.read())
        if psutil.pid_exists(pid):
            nebula_client.debug('IPCam deamon still running with PID %s' % pid)
            sys.exit()
        else:
            nebula_client.critical('IPCam deamon with PID %s crashed!' % pid)

# Register current deamon
with open(pidfile, 'w') as fp:
    pid = str(os.getpid())
    nebula_client.info('Registering IPCam deamon with PID %s' % pid)
    fp.write(pid)

# Set up IPCam clients
IPCam_motor = IPCam.Client(**cfg['ipcam']['motor'])
IPCam_garden = IPCam.Client(**cfg['ipcam']['garden'])

# Set up Pushover client
pushover_client = pushover.Client(**cfg['pushover'])

# Set up Guard House Arduino client
arduino_client = arduino.Client(**cfg['arduino'])

# Set up Hue client
hue_client = hue.Client(**cfg['hue'])

# Local variables
motor_light_state = 0
strobe_state = 0

while True:
    # Sleep for x seconds
    time.sleep(cfg['ipcam']['polling'])
    #print('Polling!')

    # Check for day/night transitions
    night = IPCam_motor.day_night()
    if night is not None:
        if arduino_client.set_value('day_night', night):
            if night:
                nebula_client.info('Transition to night written to Wemos Motor')
                # If no one home turns lights on in 'not home' mode
                if hue_client.get_all_off():
                    hue_client.set_scene('Not home')
                    nebula_client.info('Switching lights on to \'Not home\' mode')
            else:  # If not night, then day
                nebula_client.info('Transition to day written to Wemos Motor')
        else:
            nebula_client.warning('Failed to write \'day_night\' to Wemos Motor')

    # Check for new motion at Motor IPCam
    if IPCam_motor.motion_detect():
        # Alarm handling
        # print('Alarm')
        pushover_client.message('Alarm triggered!', IPCam_motor.snapshot(), 'GuardHouse Security', 'high', 'alien')

        # Strobe handling
        if not strobe_state:
            strobe_state = 1
            if arduino_client.set_value('strobe', strobe_state):
                nebula_client.debug('Wrote \'HIGH\' to \'strobe\' to Wemos Motor')
            else:
                nebula_client.warning('Failed to write \'strobe\' to Wemos Motor')

        # Light handling
        if arduino_client.get_value('day_night'):
            # It is dark out so we should turn the light on if...
            if not motor_light_state:
                # ... it is off
                motor_light_state = 1
                if arduino_client.set_value('motor_light', motor_light_state):
                    nebula_client.debug('Wrote \'HIGH\' to \'motor_light\' to Wemos Motor')
                else:
                    nebula_client.warning('Failed to write \'motor_light\' to Wemos Motor')
    else:
        # Light handling
        if IPCam_motor.motion_timeout():
            # Last change to light setting was more then the hysteresis limit, so a change is allowed
            if motor_light_state:
                # There is no motion detected and the light is on so we turn the light off
                motor_light_state = 0
                if arduino_client.set_value('motor_light', motor_light_state):
                    nebula_client.debug('Wrote \'LOW\' to \'motor_light\' to Wemos Motor')
                else:
                    nebula_client.warning('Failed to write \'motor_light\' to Wemos Motor')

            # Strobe handling
            if strobe_state:
                strobe_state = 0
                if arduino_client.set_value('strobe', strobe_state):
                    nebula_client.debug('Wrote \'LOW\' to \'strobe\' to Wemos Motor')
                else:
                    nebula_client.warning('Failed to write \'strobe\' to Wemos Motor')
        # print('Don\'t worry...')


