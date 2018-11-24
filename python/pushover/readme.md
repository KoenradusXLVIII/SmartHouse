# Simple Pushover API module

## Introduction
This is a very simple Pushover module that allows you to access the Pushover API
and transmit a message. An optional picture can be added by passing a binary 
object as the *attachment* parameter. 

## Usage example
```python
# Import modules
import yaml
import os
from pushover import client

# Load configuration YAML
path = os.path.dirname(os.path.realpath(__file__))
cfg = yaml.load(open(path + '/config.yaml','r'))

# Create Pushover instance
pushover = client(cfg['pushover']['token'], cfg['pushover']['user'], cfg['pushover']['url'])

# Send message with image attachment
fp = open('randomimage.jpg', 'rb')
pushover.message('Look at this cool picture!',fp)
```

## Configuration file example
The configuration file is not included in the repository, because it contains sensitive data. 
To make these scripts work, create a config.yaml file and use the following layout.

```
pushover:
  url   : 'https://api.pushover.net/1/messages.json'
  token : 'YOUR API TOKEN HERE'
  user  : 'YOUR USER KEY HERE'
```
