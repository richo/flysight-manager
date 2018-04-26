#!/usr/bin/env python
import sendgrid
from sendgrid.helpers.mail import *
import log

@log.make_loggable
class Mailer(object):
    def __init__(self, cfg):
        self.token = cfg.token
        self.sg = sendgrid.SendGridAPIClient(apikey=self.token)

    def mail(self, mail_to, mail_from, subject, body, headers={}):
        message = sendgrid.Mail()

        message.add_to(mail_to)
        message.set_from(mail_from)
        message.set_subject(subject)
        message.set_html(body)

        self.client.send(message)

        content = Content("text/html", body)
        mail = Mail(Email(mail_from), subject, Email(mail_to), content)

        return self.sg.client.mail.send.post(request_body=mail.get())


@log.make_loggable
class Formatter(object):
    def __init__(self, template):
        pass

    def format(self, data):
        pass
