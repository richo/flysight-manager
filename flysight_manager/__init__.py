#!/usr/bin/env python

import os
import sys
import argparse
import processors

import log
from .config import Configuration
from .file_manager import DirectoryPoller, VolumePoller
from .upload_queue import UploadQueue, UploadQueueEntry


class UnsupportedPlatformError(Exception):
    pass


def get_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--daemon', action='store_true',
                        help='Run in daemon mode')
    parser.add_argument('--noop', action='store_true',
                        help='Don\'t upload or delete anything')
    return parser


def get_poller():
    platform = sys.platform
    if platform.startswith('linux'):
        return VolumePoller
    elif platform == 'darwin':
        return DirectoryPoller
    else:
        raise UnsupportedPlatformError('Unknown platform: %s' % platform)


def main():
    args = get_argparser().parse_args()
    cfg = Configuration()
    cfg.update_with_args(args)

    wrapper = log.catch_exceptions
    if args.daemon:
        log.info("Setting up retry wrapper")
        wrapper = log.catch_exceptions_and_retry

    while True:
        log.info("Watching for flysight at %s (%s)" % (cfg.flysight_cfg.mountpoint, cfg.flysight_cfg.uuid))
        poller_class = get_poller()
        poller = poller_class(cfg.flysight_cfg.uuid)
        if args.daemon:
            poller.poll_for_attach()
        else:
            poller.raise_unless_attached()
        flysight = poller.mount(cfg.flysight_cfg.mountpoint)

        queue = UploadQueue()

        if cfg.flysight_enabled:
            raw_queue = queue.get_directory("raw")
            for flight in flysight.flights():
                raw_queue.append(UploadQueueEntry(flight.fs_path, flight.raw_path))

                for processor_name in cfg.processors:
                    processor = processors.get_processor(processor_name)(cfg)
                    processor.process(flight, queue)


            @wrapper
            def network_operations():
                """Encapsulate network operations that might fail.

                If wrapper is catch_exceptions_and_retry,
                this block may be invoked more than once, but
                that's safe.
                """
                cfg.uploader.handle_queue(queue)
            network_operations()

            log.info("Done uploading, cleaning directories")
            for date in flysight.dates():
                log.info("Removing %s" % date)
                if not cfg.noop:
                    os.rmdir(os.path.join(cfg.flysight.mountpoint, date))

            flysight.unmount()
        if not args.daemon:
            break
    log.info("Done")


if __name__ == '__main__':
    main()
