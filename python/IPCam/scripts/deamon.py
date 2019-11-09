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
import MQTT

# Constants
OFF = "0"
ON = "1"
DAY = "0"
NIGHT = "1"

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

def talk_log(msg, SNR='', level='info', verbose=True):
    """ Function to write to log and to screen simultaneously """
    if SNR:
        SNR = '[%s] ' % SNR
    if verbose:
        print('%s%s' % (SNR, msg))
    if level == 'info':
        logging.info('%s%s' % (SNR, msg))
    elif level == 'warning':
        logging.warning('%s%s' % (SNR, msg))
    logger = logging.getLogger()
    logger.handlers[0].flush()

def main():
    # Initialize logging
    init_log('IPCam deamon')

    # Load configuration YAML
    path = os.path.dirname(os.path.realpath(__file__))
    fp = open(path + '/config.yaml', 'r')
    cfg = yaml.load(fp)

    # Set up Nebula API client
    nebula_client = nebula.Client(**cfg['nebula'])
    nebula_client.set_level(nebula.INFO)

    # Set up MQTT client
    mqtt_client = MQTT.Client(**cfg['mqtt'])
    mqtt_client.subscribe('nodes/#')

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
    #IPCam_motor.set_base_path(recording_dir)
    IPCam_garden = IPCam.Client(**cfg['ipcam']['garden'])
    #IPCam_garden.set_base_path(recording_dir)

    # Set up Pushover client
    pushover_client = pushover.Client(**cfg['pushover'])

    # Set up Arduino clients
    arduino_motor = arduino.Client(**cfg['arduino']['motor'])
    arduino_guardhouse = arduino.Client(**cfg['arduino']['guardhouse'])

    # Set up Hue client
    #hue_client = hue.Client(**cfg['hue'])

    # Local variables
    last_motion = 0
    strobe = 0
    motor_light = 0

    while True:
        # Check for new motion at Motor IPCam
        if IPCam_motor.new_recording():
            # New motion detected!
            # Push alarm to smartphone
            #pushover_client.message('Alarm triggered!', IPCam_motor.snapshot(), 'GuardHouse Security', 'high', 'alien')

            # Push message to Nebula
            nebula_client.info('Alarm triggered!')

            # Strobe handling
            strobe = ON
            mqtt_client.publish(cfg['mqtt']['nodes']['motor'], cfg['mqtt']['sensors']['strobe'], ON)

            # Light handling
            day_night = mqtt_client.get_single(cfg['mqtt']['sensors']['day_night'])
            if day_night == NIGHT:
                # It is dark out so we should turn the light on
                motor_light = ON
                mqtt_client.publish(cfg['mqtt']['nodes']['motor'], cfg['mqtt']['sensors']['motor_light'], ON)

            last_motion = time.time()
        elif strobe:
            # Alarm is on, but is motion still ongoing?
            if IPCam_motor.motion_detect():
                # Motion still ongoing
                last_motion = time.time()
            else:
                # Motion no longer ongoing, wait for timeout
                if (time.time() - last_motion) > cfg['ipcam']['motion_timeout']:
                    if strobe == ON:
                        strobe = OFF
                        mqtt_client.publish(cfg['mqtt']['nodes']['motor'], cfg['mqtt']['sensors']['strobe'], OFF)
                    if motor_light == ON:
                        motor_light = OFF
                        mqtt_client.publish(cfg['mqtt']['nodes']['motor'], cfg['mqtt']['sensors']['motor_light'], OFF)

        # Check for day/night transitions
        night = IPCam_motor.delta_day_night()
        if night is not None:
            # Todo: implement check to verify message received
            mqtt_client.publish(cfg['mqtt']['nodes']['guardhouse'], cfg['mqtt']['sensors']['day_night'], night)
            if night:
                nebula_client.info('Transition to night written to Arduino Guardhouse')
                # If no one home turns lights on in 'not home' mode
                mqtt_client.publish(cfg['mqtt']['nodes']['hue'], 'scene', 'not_home')
            else:  # If not night, then day
                nebula_client.info('Transition to day written to Arduino Guardhouse')



# Start of program
if __name__ == "__main__":
    sys.excepthook = log_except_hook
    main()