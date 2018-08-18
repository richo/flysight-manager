#!/usr/bin/env python

import os
import sys
import argparse
import processors

import log
from run import Main
from .config import Configuration, get_poller
from .upload_queue import UploadQueue, UploadQueueEntry
from .report import UploadReport

from .version import VERSION

class UnsupportedPlatformError(Exception):
    pass


@log.make_loggable
class FlysightMain(Main):
    def argument_parser(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--daemon', action='store_true',
                            help='Run in daemon mode')
        parser.add_argument('--noop', action='store_true',
                            help='Don\'t upload or delete anything')
        parser.add_argument('--preserve', action='store_true',
                            help='Don\'t remove uploaded files')
        return parser

    def poller_class(self):
        return get_poller('flysight')

    def poller(self):
        return self.poller_class('flysight', self.cfg)

    def upload_run(self):
        already_seen = False
        cfg = self.cfg

        while True:
            report = self.start_report(UploadReport)
            self.info("Watching for flysight at %s (%s)" % (cfg.flysight_cfg.mountpoint, cfg.flysight_cfg.uuid))
            if self.args.daemon:
                self.poller.poll_for_attach(already_attached=already_seen)
            else:
                self.poller.raise_unless_attached()
            flysight = self.poller.mount(self.cfg.flysight_cfg.mountpoint)

            queue = UploadQueue()
            if cfg.pushover_enabled:
                queue.notify_on_completion(PushoverNotifier(
                    cfg.pushover_cfg.token,
                    cfg.pushover_cfg.user,
                    ))

            if self.cfg.flysight_enabled:
                raw_queue = queue.get_directory("raw")
                for flight in flysight.flights():
                    raw_queue.append(UploadQueueEntry(flight.fs_path, flight.raw_path))

                    for processor_name in cfg.processors:
                        processor = processors.get_processor(processor_name)(cfg)
                        processor.process(flight, queue)


                @self.wrapper(report)
                def network_operations():
                    """Encapsulate network operations that might fail.

                    If wrapper is catch_exceptions_and_retry,
                    this block may be invoked more than once, but
                    that's safe.
                    """
                    queue.process_queue(self.uploaders, preserve=global_cfg.preserve)

                network_operations()

                self.info("Done uploading, cleaning directories")
                for date in flysight.dates():
                    log.info("Removing %s" % date)
                    if not cfg.noop:
                        os.rmdir(os.path.join(cfg.flysight_cfg.mountpoint, date))

                flysight.unmount()
            if not self.args.daemon:
                break
            already_seen = True
        self.info("Done")

def main():
    FlysightMain().run()

if __name__ == '__main__':
    main()
