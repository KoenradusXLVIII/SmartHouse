# Public imports
import os
import sys
import yaml
import traceback
import paho.mqtt.client as mqtt
import time

# Private imports
from common.log import init_log, talk_log

msg_log = []


# Functions
def log_except_hook(*exc_info):
    error = ''.join(traceback.format_exception(*exc_info))
    talk_log('Unhandled exception: %s' % error, 'warning')


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    source = msg.topic.split('/')
    value = msg.payload.decode('UTF-8')
    if msg.retain:
        print('%s => %s [retained]' % (msg.topic, value))
        msg_log.append(msg)
    else:
        print('%s => %s' % (msg.topic, value))


def main():
    # Initialize logging
    init_log('MQTT Tester')

    # Load configuration YAML
    path = os.path.dirname(os.path.realpath(__file__))
    fp = open(path + '/config.yaml', 'r')
    cfg = yaml.load(fp)

    # Set up MQTT client
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(**cfg['mqtt']['credentials'])
    mqtt_client.connect(cfg['mqtt']['host'])
    mqtt_client.on_message = on_message

    # Subscribe to topic
    mqtt_client.subscribe('nodes/#')
    mqtt_client.loop_start()
    time.sleep(.1)
    mqtt_client.loop_stop()

    print(msg_log)


# Start of program
if __name__ == "__main__":
    sys.excepthook = log_except_hook
    main()