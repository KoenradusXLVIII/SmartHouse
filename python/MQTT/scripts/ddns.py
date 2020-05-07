# Global imports
import time
import sys
import paho.mqtt.client as mqtt
import os
import yaml
import uuid
import socket
from requests import get

# Main function
def main():
    # Load configuration YAML
    path = os.path.dirname(os.path.realpath(__file__))
    fp = open(path + '/config.yaml', 'r')
    cfg = yaml.safe_load(fp)

    # Set up MQTT client
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(username=cfg['mqtt']['username'], password=cfg['mqtt']['password'])
    mqtt_client.connect(cfg['mqtt']['host'], cfg['mqtt']['port'])

    # Retrieve network information
    mac = hex(uuid.getnode())
    mac = mac[2:].upper()
    hostname = socket.gethostname()
    internal_ip = socket.gethostbyname(hostname)
    external_ip = get('https://api.ipify.org').text

    # Publish to MQTT
    mqtt_client.publish('nodes/{}/hostname'.format(mac), hostname, retain=True)
    mqtt_client.publish('nodes/{}/internal_ip'.format(mac), internal_ip, retain=True)
    mqtt_client.publish('nodes/{}/external_ip'.format(mac), external_ip, retain=True)

    # Blocking call that processes network traffic, dispatches callbacks and  handles reconnecting.
    mqtt_client.loop_start()
    time.sleep(5)
    mqtt_client.loop_stop()
    sys.exit()


if __name__ == '__main__':
    main()
