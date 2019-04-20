import requests


class Client:
    def __init__(self, api_key, city):
        self.api_key = api_key
        self.city = city
        self.today_high_temperature = ''
        self.qpf_allday = []
        self.temp = ''
        self.humi = ''
        self.wind = ''
        self.pressure = ''
        self.visibility = ''

    def generate_url(self, function):
        return 'http://api.wunderground.com/api/' + self.api_key + '/' + function + '/q/' + self.city + '.json'

    def all(self):
        self.forecast10day()
        self.conditions()

    def forecast10day(self):
        try:
            # Get data from WU API
            url = self.generate_url('forecast10day')
            data = requests.get(url).json()

            # Store relevant values
            self.today_high_temperature = int(data['forecast']['simpleforecast']['forecastday'][0]['high']['celsius'])
            self.qpf_allday.clear()
            for d in range(0, 10):
                self.qpf_allday.append(int(data['forecast']['simpleforecast']['forecastday'][d]['qpf_allday']['mm']))

            # Return success
            return True
        except ConnectionError:
            # Return failure
            return False

    def conditions(self):
        try:
            # Get data from WU API
            url = self.generate_url('conditions')
            data = requests.get(url).json()

            # Store relevant values
            self.temp = float(data['current_observation']['temp_c'])
            self.humi = float(data['current_observation']['relative_humidity'].strip('%'))
            self.wind = float(data['current_observation']['wind_kph'])
            self.pressure = float(data['current_observation']['pressure_mb'])
            self.visibility = float(data['current_observation']['visibility_km'])

            # Return success
            return True
        except ConnectionError:
            # Return failure
            return False
        except KeyError:
            # Retrieved data not valid
            return False


