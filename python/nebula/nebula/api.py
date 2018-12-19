import requests
import json


class Client:
    def __init__(self, url, api_key):
        self.url = url
        self.api_key = api_key
        self.payload = {}
        self.payload['api_key'] = api_key
        self.payload['values'] = []

    def get_meas(self):
        url = self.url + '/api/meas/read.php'
        r = requests.get(url).json()
        return r['records']

    def add_meas(self, sensor_id, value):
        url = self.url + '/api/meas/create.php'
        self.payload['values'].append({'sensor_id': sensor_id, 'value': '%.2f' % (value)})

    def post_payload(self):
        r = requests.post(self.url, json=self.payload)
        self.payload['values'] = []

    def get_payload(self):
        return self.payload


