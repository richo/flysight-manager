#!/usr/bin/env python

import log
import time
from jinja2 import Template
import traceback


class Report(object):
    TIME_FMT = ": %y/%m/%d %H:%M %z (%Z)"

    def __init__(self):
        self.logs = log.LogAggregator.new()
        self.started = time.strftime(self.TIME_FMT)


def format_exception_as_reason(exc):
    return traceback.format_exc(exc)


@log.make_loggable
class UploadReport(Report):

    TEMPLATE_FILENAME = 'templates/uploader_report.jinja2'

    def __init__(self, mailer, mail_cfg):
        self.files = []
        self.mailer = mailer
        self.mail_cfg = mail_cfg
        self.reason = None
        super(UploadReport, self).__init__()

    def add_uploaded_file(self, filename):
        self.files.append(filename)

    def finish_with_reason(self, reason):
        self.reason = reason
        self.finish()

    def finish_with_exception(self, exc):
        self.reason = format_exception_as_reason(exc)
        self.finish()

    def finish(self):
        pass

    def render(self):
        tpl = Template(open(self.TEMPLATE_FILENAME).read())
        return tpl.render(
            reason=self.reason,
            files=self.files,
            logs=self.logs
        )

    def send(self):
        content = self.render()
        self.mailer.mail(
            self.mail_cfg['to'],
            self.mail_cfg['from'],
            self.mail_cfg['subject'] + self.started,
            content
        )
