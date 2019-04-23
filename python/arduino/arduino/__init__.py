import requests


class Client:
    def __init__(self, ip):
        self.url = 'http://' + ip + '/'
        self.retries = 3
        self.timeout = 1    # second

    def get_value(self, var, itt = 0):
        url = self.url + var.lower()
        try:
            r = requests.get(url, timeout=self.timeout).json()
            return float(r[var.lower()])
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout):
            itt += 1
            if itt < self.retries:
                self.get_value(var, itt)
            else:
                return None

    def get_all(self, itt=0):
        url = self.url + 'all'
        try:
            r = requests.get(url, timeout=self.timeout).json()
            return r
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout):
            itt += 1
            if itt < self.retries:
                self.get_all(itt)
            else:
                return None

    def set_value(self, var, value, itt = 0):
        url = self.url + var.lower() + '/' + str(value)
        try:
            r = requests.get(url, timeout=self.timeout).json()
            if float(r[var.lower()]) == float(value):
                return True
            else:
                return None
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout):
            itt += 1
            if itt < self.retries:
                self.set_value(var, value, itt)
            else:
                return None

