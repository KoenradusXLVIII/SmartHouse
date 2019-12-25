# Public imports
import os
import sys
import yaml
import platform
import psutil
import traceback
import logging
import time
from datetime import datetime
import paho.mqtt.client as mqtt

# Private imports
import hue

# Load configuration YAML
path = os.path.dirname(os.path.realpath(__file__))
fp = open(path + '/config.yaml', 'r')
cfg = yaml.load(fp)

# Set up Hue client
hue_client = hue.Client(cfg['hue']['ip'])

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

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    if not msg.retain:
        msg.payload = msg.payload.decode('UTF-8')
        talk_log('%s => [%s]' % (msg.topic, msg.payload))
        if msg.payload == 'Not home':
            hue_client.set_scene(msg.payload)
        elif msg.payload == 'All off':
            hue_client.set_all_off();

# Main function
def main():
    # Start deamon
    # PID file location
    if platform.system() == 'Windows':
        pidfile = 'c:\\tmp\\Hue_MQTT_daemon.pid'
    elif platform.system() == 'Linux':
        pidfile = '/tmp/Hue_MQTT_daemon.pid'

    # Check if deamon already running
    if os.path.isfile(pidfile):
        with open(pidfile, 'r') as fp:
            pid = int(fp.read())
            if psutil.pid_exists(pid):
                sys.exit()

    # Initialize logging
    init_log('Hue_MQTT_bridge')

    # Register current deamon
    with open(pidfile, 'w') as fp:
        pid = str(os.getpid())
        talk_log('Registering recording checker with PID %s' % pid, 'info')
        fp.write(pid)

    # Set up MQTT client
    mqtt_client = mqtt.Client()
    mqtt_client.on_message = on_message
    mqtt_client.username_pw_set(username=cfg['mqtt']['username'], password=cfg['mqtt']['password'])
    mqtt_client.connect(cfg['mqtt']['host'], cfg['mqtt']['port'])
    mqtt_client.subscribe("hue/#")

    # Local initialisation
    last_published_scene = ''
    start_time = time.time() - cfg['hue']['refresh_rate']

    while True:
        time.sleep(1)
        mqtt_client.loop()

        if time.time() - start_time > cfg['hue']['refresh_rate']:
            if hue_client.get_all_off():
                current_scene = 'All off'
            elif hue_client.check_scene_active(cfg['hue']['scenes']['not home']):
                current_scene = 'Not home'
            else:
                current_scene = 'Home'

            if current_scene is not last_published_scene:
                last_published_scene = current_scene
                mqtt_client.publish('hue/scene', current_scene, retain=True)


# Start of program
if __name__ == "__main__":
    sys.excepthook = log_except_hook
    main()



