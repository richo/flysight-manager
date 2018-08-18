#!/usr/bin/env python

import argparse

import log
from .run import Main
from .config import get_poller
from .upload_queue import UploadQueue, UploadQueueEntry
from .uploader import VimeoUploader, YoutubeUploader
from .report import UploadReport
from .notifier import PushoverNotifier
from .file_manager import GroupPoller


class UnsupportedPlatformError(Exception):
    pass


class Camera(object):
    pass


def get_attached_cameras(cameras):
    return filter(lambda x: x.poller.device_attached("DCIM"), cameras.values())


@log.make_loggable
class GoProMain(Main):
    def configure_uploaders(self):
        if self.cfg.vimeo_enabled:
            self.uploaders.insert(0, VimeoUploader(self.cfg.vimeo_cfg.token, self.cfg.noop))
        if self.cfg.youtube_enabled:
            self.uploaders.insert(0, YoutubeUploader(self.cfg.youtube_cfg, self.cfg.noop))

    def argument_parser(self):
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

    def poller_class(self):
        return get_poller('gopro')

    def wait_for_attach(self, cameras):
        if self.args.daemon:
            group = GroupPoller(map(lambda x: x.poller, cameras.values()))
            group.poll_for_attach()
            attached_cameras = get_attached_cameras(cameras)
        else:
            attached_cameras = get_attached_cameras(cameras)
            if len(attached_cameras) == 0:
                log.fatal("No cameras attached")
        return attached_cameras

    def upload_run(self):
        cameras = {}
        for name, cfg in self.cfg.gopro_cfg.cameras().items():
            camera = Camera()
            camera.name = name
            camera.cfg = cfg
            camera.poller = self.poller_class(name, cfg)
            cameras[name] = camera

        while True:
            report = self.start_report(UploadReport)
            mountpoints, uuids = zip(*map(lambda x: (x.cfg.mountpoint, x.cfg.uuid), cameras.values()))
            self.info("Watching for gopros at %s (%s)" % (mountpoints, uuids))

            attached_cameras = self.wait_for_attach(cameras)

            for camera in attached_cameras:
                self.info("Uploading video files from %s" % camera.name)
                gopro = camera.poller.mount(camera.cfg.mountpoint)

                queue = UploadQueue()
                if cfg.pushover_enabled:
                    queue.notify_on_upload(PushoverNotifier(
                        cfg.pushover_cfg.token,
                        cfg.pushover_cfg.user,
                    ))

                raw_queue = queue.get_directory(camera.name)
                for video in gopro.videos():
                    raw_queue.append(UploadQueueEntry(video.fs_path, video.upload_path))

                @self.wrapper(report)
                def network_operations():
                    """Encapsulate network operations that might fail.

                    If wrapper is catch_exceptions_and_retry,
                    this block may be invoked more than once, but
                    that's safe.
                    """
                    queue.process_queue(self.uploaders, preserve=self.global_cfg.preserve, report=report)
                network_operations()

                self.info("Done uploading")
            if not self.args.daemon:
                break
        self.info("Done")


def main():
    GoProMain().run()


if __name__ == '__main__':
    main()
