#!/usr/bin/env python

import log
from jinja2 import Template
import traceback

class Report(object):
    @classmethod
    def start(cls):
        report = cls()

        return report



@log.make_loggable
class UploadReport(Report):

    TEMPLATE_FILENAME = 'templates/uploader_report.jinja2'

    def __init__(self, mailer, mail_cfg):
        self.files = []
        self.mailer = mailer
        self.mail_cfg = mail_cfg

    def add_uploaded_file(self, filename):
        self.files.append(filename)

    def finish_with_exception(self, exc):
        reason = format_exception_as_reason(exc)
        self.finish

    def finish(self, reason):
        self.reason = reason

    def render(self):
        tpl = Template(TEMPLATE_FILENAME)
        return tpl.render(
                reason=self.reason,
                files=self.files,
                )

    def send(self):
        content = self.render()
        self.mailer.mail(
                self.mail_cfg['to'],
                self.mail_cfg['from'],
                self.mail_cfg['subject'],
                content)
