import os
import subprocess
import time

import log
from .flysight import Flysight
from .gopro import GoPro


class NotMountedError(Exception):
    """Flysight was not detected"""
    pass


class AbstractPoller(object):

    device_paths = {
            'flysight': 'config.txt',
            'gopro': 'DCIM',
            }

    def __init__(self, name, ty):
        self.interval = 10
        self.ty = ty
        self.name = name

    def poll_for_attach(self, already_attached=False, immediate_return=None):
        if already_attached:
            while self._flysight_attached():
                log.debug("%s still attached, waiting for disconnect" % self.ty)
                time.sleep(self.interval * 30)
            log.debug("%s disconnected" % self.ty)
        while not self._flysight_attached():
            log.debug("%s does not exist, sleeping for %ds" %
                      (self.device_path(), self.interval))
            if immediate_return:
                log.debug("Shortcircuiting timeout")
                return
            time.sleep(self.interval)

    def raise_unless_attached(self):
        path = self.device_paths[self.ty]

        if not self.device_attached(path):
            raise NotMountedError("%s is not mounted" % self.ty)

    def mount(self):
        raise NotImplementedError

    def device_class(self):
        return {
            'flysight': Flysight,
            'gopro': GoPro,
        }[self.ty]


class DirectoryPoller(AbstractPoller):
    def __init__(self, name, path, ty):
        self.path = path
        super(DirectoryPoller, self).__init__(name, ty)

    def device_attached(self, path):
        return os.path.exists(os.path.join(self.path, path))

    def mount(self, _):
        return self.device_class()(self.name, self.path)


class VolumePoller(AbstractPoller):
# TODO Make this unmount on exit always
    def __init__(self, name, uuid, ty):
        self.uuid = uuid
        super(VolumePoller, self).__init__(name, ty)

    def device_path(self):
        return os.path.join('/', 'dev', 'disk', 'by-uuid', self.uuid)

    def device_attached(self, _):
        return os.path.exists(self.device_path())

    def mount(self, path):
        subprocess.check_call(['sudo', 'mount', self._flysight_path(), path])
        log.info("Mounted %s on %s" % (self._flysight_path(), path))
        return self.device_class()(self.name, self.path)
