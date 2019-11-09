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

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    if not msg.retain:
        # Only handle new messages
        print('%s => %s' % (msg.topic, msg.payload.decode('UTF-8')))

# Main function
def main():
    # Set up MQTT client
    mqtt_client = mqtt.Client()
    mqtt_client.on_message = on_message
    mqtt_client.username_pw_set(username='pi', password='raspberry')
    mqtt_client.connect('192.168.1.114', 1883, 60)
    mqtt_client.subscribe("nodes/#")

    # Blocking call that processes network traffic, dispatches callbacks and  handles reconnecting.
    mqtt_client.loop_forever()


if __name__ == '__main__':
    main()
