#!/usr/bin/env python

import os
import sys
import argparse
import processors

import log
from .config import Configuration, get_poller
from .upload_queue import UploadQueue, UploadQueueEntry
from .uploader import VimeoUploader, YoutubeUploader


class UnsupportedPlatformError(Exception):
    pass


def get_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--daemon', action='store_true',
                        help='Run in daemon mode')
    parser.add_argument('--camera', action='store',
                        help='Camera to watch', default=False)
    parser.add_argument('--noop', action='store_true',
                        help='Don\'t upload or delete anything')
    parser.add_argument('--preserve', action='store_true',
                        help='Don\'t remove uploaded files')
    return parser

class Camera(object):
    pass

def get_attached_cameras(cameras):
    return filter(lambda x: x.poller.device_attached("DCIM"), cameras.values())

def main():
    args = get_argparser().parse_args()
    cfg = Configuration()
    cfg.update_with_args(args)
    uploader = cfg.uploader
    global_cfg = cfg

    wrapper = log.catch_exceptions
    if args.daemon:
        log.info("Setting up retry wrapper")
        wrapper = log.catch_exceptions_and_retry

    poller_class = get_poller('gopro')

    uploaders = [uploader]
    if cfg.vimeo_enabled:
        uploaders.insert(0, VimeoUploader(cfg.vimeo_cfg.token, cfg.noop))
    if cfg.youtube_enabled:
        uploaders.insert(0, YoutubeUploader(cfg.youtube_cfg.token, cfg.noop))

    cameras = {}
    for name, cfg in cfg.gopro_cfg.cameras().items():
        camera = Camera()
        camera.name = name
        camera.cfg = cfg
        camera.poller = poller_class(name, cfg)
        cameras[name] = camera

    already_seen = False

    while True:
        mountpoints, uuids = zip(*map(lambda x: (x.cfg.mountpoint, x.cfg.uuid), cameras.values()))
        log.info("Watching for gopros at %s (%s)" % (mountpoints, uuids))

        attached_cameras = get_attached_cameras(cameras)
        if args.daemon:
            poller.poll_for_attach(already_attached=already_seen)
        else:
            if len(attached_cameras) == 0:
                raise RuntimeError("No cameras attached")

        for camera in attached_cameras:
            gopro = camera.poller.mount(camera.cfg.mountpoint)

            queue = UploadQueue()

            raw_queue = queue.get_directory(camera.name)
            for video in gopro.videos():
                raw_queue.append(UploadQueueEntry(video.fs_path, video.upload_path))


            @wrapper
            def network_operations():
                """Encapsulate network operations that might fail.

                If wrapper is catch_exceptions_and_retry,
                this block may be invoked more than once, but
                that's safe.
                """
                queue.process_queue(uploaders, preserve=global_cfg.preserve)
            network_operations()

            log.info("Done uploading")

            gopro.unmount()
        if not args.daemon:
            break
        already_seen = True
    log.info("Done")


if __name__ == '__main__':
    main()
