import requests
import datetime


class Client:
    def __init__(self, api_key, city, retries=3, timeout=1):
        self.api_key = api_key
        self.city = city
        self.retries = retries
        self.timeout = timeout
        self.temp_forecast = [0, 0, 0]  # degC
        self.rain_forecast = [0, 0, 0]  # mm
        self.temp = 0       # degC
        self.pressure = 0   # hPa
        self.humidity = 0   # %
        self.wind = 0       # m/s

        # Local variables
        self._base_url = 'https://api.openweathermap.org/data/2.5/'

    def forecast(self, itt=0):
        url = self._base_url + 'forecast?q=' + self.city + '&appid=' + self.api_key
        try:
            r = requests.get(url, timeout=self.timeout).json()
            for day in range(0, len(self.temp_forecast)):
                for forecast in r['list']:
                    date = (datetime.date.today() + datetime.timedelta(days=day)).strftime('%Y-%m-%d')
                    if date in forecast['dt_txt']:
                        try:
                            self.temp_forecast[day] = max(self.temp_forecast[day], self._KtoC(forecast['main']['temp']))
                            self.rain_forecast[day] += forecast['rain']['3h']
                        except KeyError:
                            continue
            return True
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout):
            itt += 1
            if itt < self.retries:
                self.forecast(itt)
            else:
                return False

    def weather(self, itt=0):
        url = self._base_url + 'weather?q=' + self.city + '&appid=' + self.api_key
        try:
            r = requests.get(url, timeout=self.timeout).json()
            self.temp = self._KtoC(r['main']['temp'])
            self.pressure = r['main']['pressure']
            self.humidity = r['main']['humidity']
            self.wind = r['wind']['speed']
            return True
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout):
            itt += 1
            if itt < self.retries:
                self.forecast(itt)
            else:
                return False


    def _KtoC(self, val):
        # Convert temperature in Kelvin to Celsius
        return val - 273.15
