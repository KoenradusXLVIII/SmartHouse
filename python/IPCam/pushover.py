import requests

class client:
    def __init__(self, token, user, url):
        self.token = token
        self.user = user
        self.url = url

    def message(self, message, attachment=''):
        r = requests.post(self.url,
                data={
                    "token": self.token,
                    "user": self.user,
                    "message": message
                },
                files={
                    "attachment": attachment
                })