# Global imports
import os
import yaml
import paho.mqtt.client as mqtt

# Local imports
import nebula

# Load configuration YAML
path = os.path.dirname(os.path.realpath(__file__))
fp = open(path + '/config.yaml', 'r')
cfg = yaml.load(fp)

# Set up Nebula API client
nebula_client = nebula.Client(**cfg['nebula'])

# Main function
def main():
    # Set up MQTT client
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(username='nctegdja', password='xq2_4XdhpCCK')
    mqtt_client.connect('farmer.cloudmqtt.com', 13173)
    mqtt_client.publish('nodes/840D8E8F43A1/sensors/7', '', retain=True)

    # Blocking call that processes network traffic, dispatches callbacks and  handles reconnecting.
    mqtt_client.loop_forever()


if __name__ == '__main__':
    main()
