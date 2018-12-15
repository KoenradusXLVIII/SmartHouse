import requests


class Client:
    def __init__(self, url):
        self.url = url

    def get_url(self):
        return self.url

    def set_url(self, url):
        self.url = url

    def get_value(self,var):
        url = self.url + var.lower()
        r = requests.get(url).json()
        return r[var.lower()]

    def get_all(self):
        url = self.url + 'all'
        r = requests.get(url).json()
        return r

    def set_value(self, var, value):
        url = self.url + var.lower() + '/' + str(value)
        r = requests.get(url).json()
        if r[var.lower()] == int(value):
            return True
