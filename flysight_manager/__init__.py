#!/usr/bin/env python

import os
import sys
import argparse

import log
from .config import Configuration
from .file_manager import DirectoryPoller, VolumePoller


class UnsupportedPlatformError(Exception):
    pass


def get_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--daemon', action='store_true',
                        help='Run in daemon mode')
    parser.add_argument('--mountpoint', action='store', default=None,
                        help='Find flysight at MOUNTPOINT')
    parser.add_argument('--noop', action='store_true',
                        help='Don\'t upload or delete anything')
    return parser


def get_poller():
    # TODO: This does the wrong thing if you specify --mountpoint on linux
    platform = sys.platform
    if platform.startswith('linux'):
        return DevicePoller
    elif platform == 'darwin':
        return DirectoryPoller
    else:
        raise UnsupportedPlatformError('Unknown platform: %s' % platform)


@log.catch_exceptions
def main():
    args = get_argparser().parse_args()
    cfg = Configuration()
    cfg.update_with_args(args)

    wrapper = log.catch_exceptions
    if args.daemon:
        log.info("Setting up retry wrapper")
        wrapper = log.catch_exceptions_and_retry

    while True:
        log.info("Watching for flysight at %s" % cfg.flysight_mountpoint)
        poller = get_poller(cfg.flysight_mountpoint)
        if args.daemon:
            poller.poll_for_attach()
        else:
            poller.raise_unless_attached()
        flysight = poller.mount(cfg.flysight_mountpoint)

        @wrapper
        def network_operations():
            """Encapsulate network operations that might fail.

            If wrapper is catch_exceptions_and_retry,
            this block may be invoked more than once, but
            that's safe.
            """
            for flight in flysight.flights():
                with open(flight.fs_path, 'rb') as fh:
                    cfg.uploader.upload(fh, flight.raw_path)
                log.info("Removing %s" % flight.fs_path)
                os.unlink(flight.fs_path)
        network_operations()

        log.info("Done uploading, cleaning directories")
        for date in flysight.dates():
            log.info("Removing %s" % date)
            os.rmdir(os.path.join(cfg.flysight_mountpoint, date))

        flysight.unmount()
        if not args.daemon:
            break
    log.info("Done")


if __name__ == '__main__':
    main()
