import requests


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

    def add_single(self, sensor_id, value):
        self.payload['values'].append({'sensor_id': sensor_id, 'value': '%.2f' % value})

    def add_many(self, payload):
        for sensor_id, value in payload.items():
            self.add_single(sensor_id, value)

    def post_payload(self):
        url = self.url + '/api/meas/post.php'
        r = requests.post(url, json=self.payload)
        self.payload['values'] = []

    def get_payload(self):
        return self.payload


