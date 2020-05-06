# Global imports
import time
import sys
import paho.mqtt.client as mqtt
import os
import yaml
import requests

# Private imports
import IPCam

# Main function
def main():
    # Load configuration YAML
    path = os.path.dirname(os.path.realpath(__file__))
    fp = open(path + '/config.yaml', 'r')
    cfg = yaml.load(fp)

    # Set up MQTT client
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(username='vjmpotre', password='#ukELk48z0js')
    mqtt_client.connect('joostverberk.nl', 1883)
    IPCam_motor = IPCam.Client(**cfg['ipcam']['motor'])

    mqtt_client.publish('nodes/90A2DA0EC568/sensors/20', '1', retain=True)
    #mqtt_client.publish('hue/scene', 'all_off', retain=True)
    #mqtt_client.publish('nodes/00626E6DF34/image', IPCam_motor.snapshot(), retain=False)

    # Blocking call that processes network traffic, dispatches callbacks and  handles reconnecting.
    mqtt_client.loop_start()
    time.sleep(5)
    mqtt_client.loop_stop()
    sys.exit()


if __name__ == '__main__':
    main()
