import yaml
import os
from pushover import client

# Load configuration YAML
path = os.path.dirname(os.path.realpath(__file__))
cfg = yaml.load(open(path + '/config.yaml','r'))

pushover = client(cfg['pushover']['token'], cfg['pushover']['user'], cfg['pushover']['url'])

fp = open('C:/Users/Joost/Desktop/zevenheuvelen.png', 'rb')

pushover.message('Super race!',fp)
