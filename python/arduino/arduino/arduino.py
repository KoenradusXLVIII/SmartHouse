import requests
variables = {'temp': 'Temperature',
             'humi': 'Humidity',
             'rain': 'Rain',
             'soil_humi': 'Soil Humidity',
             'door_state': 'Door state',
             'light_state': 'Light state',
             'light_delay': 'Light delay'}


class Client:
    def __init__(self, url):
        self.url = url

    def get_url(self):
        return self.url

    def set_url(self, url):
        self.url = url

    def get_value(self,var):
        if var in variables:
            url = self.url + var
            r = requests.get(url).json()
            return r[variables[var]]

    def set_value(self, var, value):
        if var in variables:
            url = self.url + var + '/' + str(value)
            r = requests.get(url).json()
            if r[variables[var]] == int(value):
                return value
