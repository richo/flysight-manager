#!/usr/bin/env python
import sendgrid
import log

@log.make_loggable
class Mailer(object):
    def __init__(self, cfg):
        self.token = cfg.token
        self.client = sendgrid.SendGridClient(self.token)

    def mail(self, mail_to, mail_from, subject, body, headers={}):
        message = sendgrid.Mail()

        message.add_to(mail_to)
        message.set_from(mail_from)
        message.set_subject(subject)
        message.set_html(body)

        self.client.send(message)
