import log
from .config import Configuration
from .mailer import Mailer


@log.make_loggable
class Main(object):
    def __init__(self):
        self.ap = self.argument_parser()
        self.args = self.ap.parse_args()

        self.cfg = Configuration()
        self.global_cfg = self.cfg

        # TODO null mailer for disabled?
        self.mailer = Mailer(self.cfg.sendgrid_cfg)

        self.cfg.update_with_args(self.args)
        self.poller_class = self.poller_class()
# XXX: Fix this for gopro
        try:
            self.poller = self.poller()
        except AttributeError:
            self.warn("Not creating poller")

        self.uploaders = [self.cfg.uploader]
        self.configure_uploaders()

        self.wrapper = log.catch_exceptions
        if self.args.daemon:
            self.info("Setting up retry wrapper")
            self.wrapper = log.catch_exceptions_and_retry

    def start_report(self, report_class):
        report = report_class(self.mailer, {
            'to': self.cfg.sendgrid_cfg.to_addr,
            'from': self.cfg.sendgrid_cfg.from_addr,
            'subject': self.cfg.sendgrid_cfg.subject,
        })
        return report

    def configure_uploaders(self):
        pass

    def poller_class(self):
        raise NotImplementedError()

    def argument_parser(self):
        raise NotImplementedError()

    def upload_run(self):
        raise NotImplementedError()

    def run(self):
        self.upload_run()
