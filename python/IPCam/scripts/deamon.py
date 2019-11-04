# Public pacakages
import yaml
import os
import time
import sys
import platform
import psutil
import traceback
import logging
from datetime import datetime

# Private packages
import IPCam
import pushover
import arduino
import nebula
import hue

# Functions
def log_except_hook(*exc_info):
    error = ''.join(traceback.format_exception(*exc_info))
    talk_log('Unhandled exception: %s' % error, 'warning')

def init_log(log_title):
    """ Initialize log file with provided title and optional COM port """
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    script_path = os.path.dirname(os.path.realpath(__file__))
    log_path = os.path.join(script_path, 'logs')
    if not os.path.exists(log_path):
        os.mkdir(log_path)
    logfileName = '%s_%s.log' % (now, log_title)
    logging.basicConfig(filename=os.path.join(script_path, 'logs', logfileName), filemode='w',
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    talk_log('Start of log \'%s\'' % os.path.join(script_path, 'logs', logfileName))

def talk_log(msg, level='info', verbose=True, nebula_client=None):
    """ Function to write to log and to screen simultaneously """
    if verbose:
        print(msg)
    if level == 'debug':
        logging.debug(msg)
        if nebula_client:
            nebula_client.debug(msg)
    elif level == 'info':
        logging.info(msg)
        if nebula_client:
            nebula_client.info(msg)
    elif level == 'warning':
        logging.warning(msg)
        if nebula_client:
            nebula_client.warning(msg)        
    elif level == 'critical':
        logging.critical(msg)
        if nebula_client:
            nebula_client.critical(msg)            
    logger = logging.getLogger()
    logger.handlers[0].flush()

def main():
    # Load configuration YAML
    path = os.path.dirname(os.path.realpath(__file__))
    fp = open(path + '/config.yaml', 'r')
    cfg = yaml.load(fp)

    # Set up Nebula API client
    nebula_client = nebula.Client(**cfg['nebula'])
    nebula_client.set_level(nebula.INFO)

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

    # Initialize logging
    init_log('IPCam deamon')

    # Register current deamon
    with open(pidfile, 'w') as fp:
        pid = str(os.getpid())
        talk_log('Registering IPCam deamon with PID %s' % pid, 'info', nebula_client=nebula_client) 
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
        # Check for day/night transitions
        night = IPCam_motor.delta_day_night()
        if night is not None:
            if arduino_guardhouse.set_value('day_night', night):
                if night:
                    talk_log('Transition to night written to Arduino Guardhouse', 'info', nebula_client=nebula_client)
                    # If no one home turns lights on in 'not home' mode
                    if hue_client.get_all_off():
                        hue_client.set_scene('Not home')
                        talk_log('Switching lights on to "Not home" mode', 'info', nebula_client=nebula_client)
                else:  # If not night, then day
                    talk_log('Transition to day written to Arduino Guardhouse', 'info', nebula_client=nebula_client)
            else:
                talk_log('Failed to write "day_night" to Arduino Guardhouse', 'warning', nebula_client=nebula_client)

        # Check for new motion at Motor IPCam
        if IPCam_motor.new_recording():
            # New motion detected!

            # Push alarm to smartphone
            pushover_client.message('Alarm triggered!', IPCam_motor.snapshot(), 'GuardHouse Security', 'high', 'alien')

            # Strobe handling
            if not strobe_state:
                strobe_state = 1
                if arduino_motor.set_value('strobe', strobe_state):
                    talk_log('Wrote "HIGH" to "strobe" to Wemos Motor', 'debug', nebula_client=nebula_client)
                else:
                    talk_log('Failed to write "strobe" to Wemos Motor', 'warning', nebula_client=nebula_client)

            # Light handling
            if arduino_guardhouse.get_value('day_night'):
                # It is dark out so we should turn the light on if...
                if not motor_light_state:
                    # ... it is off
                    motor_light_state = 1
                    if arduino_motor.set_value('motor_light', motor_light_state):
                        talk_log('Wrote "HIGH" to "motor_light" to Wemos Motor', 'debug', nebula_client=nebula_client)
                    else:
                        talk_log('Failed to write "motor_light" to Wemos Motor', 'warning', nebula_client=nebula_client)

            last_motion = time.time()
        else:
            # No new motion detected
            # Is motion still ongoing?
            if IPCam_motor.motion_detect():
                # Motion still ongoing
                last_motion = time.time()
            else: 
                # Motion no longer ongoing
                if (time.time() - last_motion) > cfg['ipcam']['motion_timeout']:
                    if motor_light_state:
                        # There is no motion detected and the light is on so we turn the light off
                        motor_light_state = 0
                        if arduino_motor.set_value('motor_light', motor_light_state):
                            talk_log('Wrote "LOW" to "motor_light" to Wemos Motor', 'debug', nebula_client=nebula_client)
                        else:
                            talk_log('Failed to write "motor_light" to Wemos Motor', 'warning', nebula_client=nebula_client)

                    # Strobe handling
                    if strobe_state:
                        strobe_state = 0
                        if arduino_motor.set_value('strobe', strobe_state):
                            talk_log('Wrote "LOW" to "strobe" to Wemos Motor', 'debug', nebula_client=nebula_client)
                        else:
                            talk_log('Failed to write "strobe" to Wemos Motor', 'warning', nebula_client=nebula_client)

        time.sleep(1)

# Start of program
if __name__ == "__main__":
    sys.excepthook = log_except_hook
    main()