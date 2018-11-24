# Foscam and Pushover

## Introduction
This script access a Foscam webcam and checks for motion detection. 
Upon detected motion this is forwarded to a smartphone by using the Pushover service. 

## Configuration file example
The configuration file is not included in the repository, because it contains sensitive data. 
To make these scripts work, create a config.yaml file and use the following layout.

```
# Foscam configuration
foscam:
  motor       :
    url       : 'http://YOURIPANDPORTHERE/'
    cgi       : 'cgi-bin/CGIProxy.fcgi'
    user      : 'YOURFOSCAMUSERNAMEHERE' # Foscam user needs admin rights to access getDevState!
    pass      : 'YOURFOSCAMPASSWORDHERE'
  state       :
    disabled  : '0'
    no alarm  : '1'
    alarm     : '2'
pushover:
  url         : 'https://api.pushover.net/1/messages.json'
  token       : 'YOURPUSHOVERTOKENHERE'
  user        : 'YOURPUSHOVERUSERKEYHERE'
