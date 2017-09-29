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

    poller_class = get_poller()
    poller = poller_class(cfg.gopro_cfg.uuid)
    already_seen = False

    while True:
        log.info("Watching for gopro at %s (%s)" % (cfg.gopro_cfg.mountpoint, cfg.gopro_cfg.uuid))
        if args.daemon:
            poller.poll_for_attach(already_attached=already_seen)
        else:
            poller.raise_unless_attached()
        gopro = poller.mount(cfg.gopro_cfg.mountpoint)

        queue = UploadQueue()

        if cfg.gopro_enabled:
            raw_queue = queue.get_directory("video")
            for video in gopro.videos():
                raw_queue.append(UploadQueueEntry(video.fs_path, video.upload_path))


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
            for video in gopro.videos():
                log.info("Removing %s" % video)
                if not cfg.noop:
                    os.unlink(video.fs_path)

            gopro.unmount()
        if not args.daemon:
            break
        already_seen = True
    log.info("Done")


if __name__ == '__main__':
    main()
