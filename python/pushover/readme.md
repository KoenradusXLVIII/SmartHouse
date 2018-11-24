# Simple Pushover API module

## Introduction
This is a very simple Pushover module that allows you to access the Pushover API
and transmit a message. An optional picture can be added by passing a binary 
object as the *attachment* parameter. 

## Configuration file example
The configuration file is not included in the repository, because it contains sensitive data. 
To make these scripts work, create a config.yaml file and use the following layout.

```
pushover:
  url   : 'https://api.pushover.net/1/messages.json'
  token : 'YOUR API TOKEN HERE'
  user  : 'YOUR USER KEY HERE'
