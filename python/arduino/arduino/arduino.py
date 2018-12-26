import requests


class Client:
    def __init__(self, ip):
        self.ip = ip
        self.url = 'http://' + ip + '/'

    def get_url(self):
        return self.url

    def set_url(self, url):
        self.url = url

    def get_value(self,var):
        url = self.url + var.lower()
        try:
            r = requests.get(url).json()
            return float(r[var.lower()])
        except:
            return None

    def get_all(self):
        url = self.url + 'all'
        try:
            r = requests.get(url).json()
            return r
        except:
            return None


    def set_value(self, var, value):
        url = self.url + var.lower() + '/' + str(value)
        try:
            r = requests.get(url).json()
            if float(r[var.lower()]) == float(value):
                return True
            else:
                return False
        except:
            return False

