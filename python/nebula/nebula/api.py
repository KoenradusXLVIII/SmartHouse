import requests
import json


class Client:
    def __init__(self, url):
        self.url = url

    def get_meas(self):
        url = self.url + '/api/meas/read.php'
        r = requests.get(url).json()
        return r['records']

    def set_meas(self, sensor_id, value):
        url = self.url + '/api/meas/create.php'
        payload = {'sensor_id': sensor_id, 'value': '%.2f' % (value)}
        r = requests.post(url, json=payload)



