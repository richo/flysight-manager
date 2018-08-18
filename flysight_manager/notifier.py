import requests


class Notifier(object):
    pass


class PushoverNotifier(Notifier):
    def __init__(self, token, user):
        self.token = token
        self.user = user

    def notify(self, message):
        return requests.post("https://api.pushover.net/1/messages.json", data={
            "token": self.token,
            "user": self.user,
            "message": message,
        })
