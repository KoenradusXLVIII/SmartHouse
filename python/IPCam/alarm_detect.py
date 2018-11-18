import requests
import os
import yaml
import time
from xml.etree import ElementTree as ET

# Load configuration YAML
path = os.path.dirname(os.path.realpath(__file__))
cfg = yaml.load(open(path + '/config.yaml','r'))

while True:
    # Read device status
    fp = requests.get(cfg['foscam']['motor'])
    root = ET.fromstring(fp.text) # Extract XML tree
    motionDetectAlarm = (root.find('motionDetectAlarm').text)
    if motionDetectAlarm == cfg['foscam']['state']['alarm']:
        break

    # Sleep for 1 second
    time.sleep(5)

