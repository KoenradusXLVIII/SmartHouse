import requests
import datetime


class Client:
    def __init__(self, api_key, city, retries=3, timeout=1):
        self.api_key = api_key
        self.city = city
        self.retries = retries
        self.timeout = timeout
        self.temp = [0, 0, 0]  # degC
        self.rain = [0, 0, 0]  # mm

        # Local variables
        self._base_url = 'https://api.openweathermap.org/data/2.5/'

    def forecast(self, itt=0):
        url = self._base_url + 'forecast?q=' + self.city + '&appid=' + self.api_key
        try:
            r = requests.get(url, timeout=self.timeout).json()
            for day in range(0, len(self.temp)):
                for forecast in r['list']:
                    date = (datetime.date.today() + datetime.timedelta(days=day)).strftime('%Y-%m-%d')
                    if date in forecast['dt_txt']:
                        self.temp[day] = max(self.temp[day], self._KtoC(forecast['main']['temp']))
                        try:
                            self.rain[day] += forecast['rain']['3h']
                        except KeyError:
                            continue
            return True
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout):
            itt += 1
            if itt < self.retries:
                self.forecast(itt)
            else:
                return False
        #except KeyError:
        #    return False

    def _KtoC(self, val):
        # Convert temperature in Kelvin to Celsius
        return val - 273.15
