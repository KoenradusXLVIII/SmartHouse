# Public packages
import sys
import yaml
import os

# Personal packages
import P1
import MQTT

# Load configuration YAML
path = os.path.dirname(os.path.realpath(__file__))
fp = open(path + '/config.yaml', 'r')
cfg = yaml.safe_load(fp)

# Set up MQTT client
mqtt_client = MQTT.Client(**cfg['mqtt'])
mqtt_client.subscribe(cfg['mqtt']['topic'])

# Set up P1 client
p1_client = P1.Client(cfg['P1']['port'])

def main():
    # Get P1 data
    if not p1_client.read_telegram():
        sys.exit()

    mqtt_client.publish('B827EBF288F8', 22, p1_client.energy)
    mqtt_client.publish('B827EBF288F8', 94, p1_client.power)

if __name__ == "__main__":
    main()
