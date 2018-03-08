import log
from .config import Configuration, get_poller

class Main(object):
    def __init__(self):
        self.ap = self.argument_parser()
        self.poller_class = self.poller_class()
        self.poller = self.poller()

        self.args = self.ap.parse_args()

        self.cfg = Configuration()
        self.global_cfg = self.cfg
        self.cfg.update_with_args(self.args)

        self.uploaders = [self.cfg.uploader]
        self.configure_uploaders()

        self.wrapper = log.catch_exceptions
        if self.args.daemon:
            self.info("Setting up retry wrapper")
            self.wrapper = log.catch_exceptions_and_retry

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
log.make_loggable(Main)
