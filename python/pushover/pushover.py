import requests

class Pushover:
    def __init__(self, token, user):
        self.token = token
        self.user = user
        self.url = 'https://api.pushover.net/1/messages.json'
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