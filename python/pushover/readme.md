# Simple Pushover API module

## Introduction
This is a very simple Pushover module that allows you to access the Pushover API
and transmit a message. An optional picture can be added by passing a binary 
object as the *attachment* parameter. Other optional parameters are 
*title*, *priority* and *sound*. For more information about how to use the parameters, 
please see the [Pushover API documentation](https://pushover.net/api).


## Usage example
```python
# Import modules
import yaml
from pushover import client

# Load configuration YAML
fp = open('config.yaml','r')
cfg = yaml.load(fp)

# Create Pushover instance
pushover = client(cfg['pushover']['token'], cfg['pushover']['user'], cfg['pushover']['url'])

# Send simple message
pushover.message('Hello world!')

# Send message with image attachment
fp = open('randomimage.jpg', 'rb')
pushover.message('Look at this cool picture!',fp)

# Send high priority message with custom title (without attachment)
pushover.message('Important message!','','Help!',cfg['pushover']['priority']['high'])
```

## Configuration file example
The configuration file is not included in the repository, because it contains sensitive data. 
To make these scripts work, create a config.yaml file and use the following layout.

```
pushover:
  url   : 'https://api.pushover.net/1/messages.json'
  token : 'YOUR API TOKEN HERE'
  user  : 'YOUR USER KEY HERE'
  priority    :
    lowest    : -2  # No notifications
    low       : -1  # No sound/vibration, but does generate pop-up
    normal    : 0   # Sound and vibration, but not in quiet hours
    high      : 1   # Sound and vibration, even in quiet hours  
```
