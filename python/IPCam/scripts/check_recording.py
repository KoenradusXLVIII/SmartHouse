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
import MQTT

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

def talk_log(msg, level='info', verbose=True):
    """ Function to write to log and to screen simultaneously """
    if verbose:
        print(msg)
    if level == 'debug':
        logging.debug(msg)
    elif level == 'info':
        logging.info(msg)
    elif level == 'warning':
        logging.warning(msg)
    elif level == 'critical':
        logging.critical(msg)
    logger = logging.getLogger()
    logger.handlers[0].flush()

def main():
    # Load configuration YAML
    path = os.path.dirname(os.path.realpath(__file__))
    fp = open(path + '/config.yaml', 'r')
    cfg = yaml.safe_load(fp)

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
                sys.exit()

    # Initialize logging
    init_log('Recording_checker')

    # Register current deamon
    with open(pidfile, 'w') as fp:
        pid = str(os.getpid())
        talk_log('Registering recording checker with PID %s' % pid, 'info')
        fp.write(pid)

    # Set up MQTT client
    mqtt_client = MQTT.Client(**cfg['mqtt'])
    mqtt_client.subscribe('nodes/#')

    # Set up IPCam clients
    IPCam_motor = IPCam.Client(**cfg['ipcam']['motor'])
    IPCam_motor.set_base_path(recording_dir)

    # Local variables
    last_motion = 0
    alarm_on = False;

    while True:
        time.sleep(0.1)
        # Check for new motion at Motor IPCam, unless the alarm or the light is already on
        if IPCam_motor.new_recording():
            talk_log('New motion detected!')
            mqtt_client.publish(cfg['mqtt']['nodes']['smarthouse'], 93, 1)
            mqtt_client.publish_image('00626E6DF34', IPCam_motor.snapshot())
            last_motion = time.time()
            alarm_on = True;
        elif alarm_on:
            # Alarm on, but is motion still ongoing?
            if IPCam_motor.motion_detect():
                # Motion still ongoing
                last_motion = time.time()
            else:
                # Motion no longer ongoing, wait for timeout
                if (time.time() - last_motion) > cfg['ipcam']['motion_timeout']:
                    talk_log('Motion ended')
                    mqtt_client.publish(cfg['mqtt']['nodes']['smarthouse'], 93, 0)
                    alarm_on = False


# Start of program
if __name__ == "__main__":
    sys.excepthook = log_except_hook
    main()
