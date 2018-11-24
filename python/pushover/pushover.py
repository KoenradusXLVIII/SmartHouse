import requests

class client:
    def __init__(self, token, user, url):
        self.token = token
        self.user = user
        self.url = url
        self.prio = {'lowest':-2,'low':-1,'normal':0,'high':1}

    def message(self, message, attachment='', title='', priority='normal', sound=''):
        r = requests.post(self.url,
                data={
                    "token": self.token,
                    "user": self.user,
                    "message": message,
                    "title": title,
                    "priority": self.prio[priority],
                    "sound": sound
                },
                files={
                    "attachment": attachment
                })