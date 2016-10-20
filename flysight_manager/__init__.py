#!/usr/bin/env python

import os
import argparse

import log
from .config import Configuration
from .file_manager import MountPoller, Unmounter
from .flysight import Flysight


def get_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--daemon', action='store_true',
                        help='Run in daemon mode')
    parser.add_argument('--mountpoint', action='store', default=None,
                        help='Find flysight at MOUNTPOINT')
    return parser


@log.catch_exceptions
def main():
    args = get_argparser().parse_args()
    cfg = Configuration()
    cfg.update_with_args(args)

    while True:
        log.info("Watching for flysight at %s" % cfg.flysight_mountpoint)
        poller = MountPoller(cfg.flysight_mountpoint)
        if args.daemon:
            poller.poll_for_attach()
        else:
            poller.raise_unless_attached()
        flysight = Flysight(cfg.flysight_mountpoint)

        for flight in flysight.flights():
            with open(flight.fs_path, 'rb') as fh:
                cfg.uploader.upload(fh, flight.raw_path)
            log.info("Removing %s" % flight.fs_path)
            os.unlink(flight.fs_path)

        log.info("Done uploading, cleaning directories")
        for date in flysight.dates():
            log.info("Removing %s" % date)
            os.rmdir(os.path.join(cfg.flysight_mountpoint, date))

        Unmounter(cfg.flysight_mountpoint).unmount()
        if not args.daemon:
            break
    log.info("Done")


if __name__ == '__main__':
    main()
