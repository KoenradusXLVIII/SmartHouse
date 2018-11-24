import requests

class client:
    def __init__(self, token, user, url):
        self.token = token
        self.user = user
        self.url = url

    def message(self, message, attachment='', title='', priority=0, sound=''):
        r = requests.post(self.url,
                data={
                    "token": self.token,
                    "user": self.user,
                    "message": message,
                    "title": title,
                    "priority": priority,
                    "sound": sound
                },
                files={
                    "attachment": attachment
                })