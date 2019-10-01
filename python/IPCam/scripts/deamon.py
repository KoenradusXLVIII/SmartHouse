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
    recording_dir = 'S:\\WCAU45635050\\webcam'
elif platform.system() == 'Linux':
    pidfile = '/tmp/IPCam_daemon.pid'
    recording_dir = '/home/pi/WCAU45635050/webcam'

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
IPCam_motor.set_base_path(recording_dir)
IPCam_garden = IPCam.Client(**cfg['ipcam']['garden'])
IPCam_garden.set_base_path(recording_dir)

# Set up Pushover client
pushover_client = pushover.Client(**cfg['pushover'])

# Set up Arduino clients
arduino_motor = arduino.Client(**cfg['arduino']['motor'])
arduino_guardhouse = arduino.Client(**cfg['arduino']['guardhouse'])

# Set up Hue client
hue_client = hue.Client(**cfg['hue'])

# Local variables
motor_light_state = 0
strobe_state = 0
last_motion = 0

while True:
    try:
        # Check for day/night transitions
        night = IPCam_motor.delta_day_night()
        if night is not None:
            if arduino_guardhouse.set_value('day_night', night):
                if night:
                    nebula_client.info('Transition to night written to Arduino Guardhouse')
                    # If no one home turns lights on in 'not home' mode
                    if hue_client.get_all_off():
                        hue_client.set_scene('Not home')
                        nebula_client.info('Switching lights on to \'Not home\' mode')
                else:  # If not night, then day
                    nebula_client.info('Transition to day written to Arduino Guardhouse')
            else:
                nebula_client.warning('Failed to write \'day_night\' to Arduino Guardhouse')

        # Check for new motion at Motor IPCam
        if IPCam_motor.new_recording():
            # Alarm handling
            pushover_client.message('Alarm triggered!', IPCam_motor.snapshot(), 'GuardHouse Security', 'high', 'alien')

            # Strobe handling
            if not strobe_state:
                strobe_state = 1
                if arduino_motor.set_value('strobe', strobe_state):
                    nebula_client.debug('Wrote \'HIGH\' to \'strobe\' to Wemos Motor')
                else:
                    nebula_client.warning('Failed to write \'strobe\' to Wemos Motor')

            # Light handling
            if arduino_guardhouse.get_value('day_night'):
                # It is dark out so we should turn the light on if...
                if not motor_light_state:
                    # ... it is off
                    motor_light_state = 1
                    if arduino_motor.set_value('motor_light', motor_light_state):
                        nebula_client.debug('Wrote \'HIGH\' to \'motor_light\' to Wemos Motor')
                    else:
                        nebula_client.warning('Failed to write \'motor_light\' to Wemos Motor')

            last_motion = time.time()
        else:
            if (time.time() - last_motion) > cfg['ipcam']['motion_timeout']:
                if motor_light_state:
                    # There is no motion detected and the light is on so we turn the light off
                    motor_light_state = 0
                    if arduino_motor.set_value('motor_light', motor_light_state):
                        nebula_client.debug('Wrote \'LOW\' to \'motor_light\' to Wemos Motor')
                    else:
                        nebula_client.warning('Failed to write \'motor_light\' to Wemos Motor')

                # Strobe handling
                if strobe_state:
                    strobe_state = 0
                    if arduino_motor.set_value('strobe', strobe_state):
                        nebula_client.debug('Wrote \'LOW\' to \'strobe\' to Wemos Motor')
                    else:
                        nebula_client.warning('Failed to write \'strobe\' to Wemos Motor')

        time.sleep(1)
    except Exception as e:
        nebula_client.critical(e)



