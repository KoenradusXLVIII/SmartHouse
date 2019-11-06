import requests


class Client:
    def __init__(self, ip):
        self.url = 'http://' + ip + '/'
        self.retries = 3
        self.timeout = 1    # second

    def get_value(self, var, itt = 0):
        url = self.url + var.lower()
        try:
            r = requests.get(url, timeout=self.timeout)
            if r.status_code == 200:
                r = r.json()
                return float(r[var.lower()])
            else:
                return None
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.ReadTimeout):
            if itt < self.retries:
                self.get_value(var, itt + 1)
            else:
                return None

    def get_all(self, itt=0):
        url = self.url + 'all'
        try:
            r = requests.get(url, timeout=self.timeout)
            if r.status_code == 200:
                r = r.json()
                return r
            else:
                return None
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.ReadTimeout):
            if itt < self.retries:
                self.get_all(itt + 1)
            else:
                return None

    def set_value(self, var, value, itt=0):
        url = self.url + var.lower() + '/' + str(value)
        try:
            r = requests.get(url, timeout=self.timeout)
            if r.status_code == 200:
                r = r.json()
                if float(r[var.lower()]) == float(value):
                    return True
                else:
                    return None
            else:
                return None

        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.ReadTimeout):
            if itt < self.retries:
                self.set_value(var, value, itt + 1)
            else:
                return None

