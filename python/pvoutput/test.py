import urllib
import json

url = "http://192.168.1.112/"
response = urllib.urlopen(url)
data = json.loads(response.read())

print data
print data['Temperature']
print data['Humidity']
