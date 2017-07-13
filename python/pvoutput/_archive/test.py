import urllib
import json

url = "http://192.168.1.112/all"
response = urllib.urlopen(url)
data = json.loads(response.read())

print data
print data['Temperature']
print data['Humidity']

print("0x{:04x}".format(3))
