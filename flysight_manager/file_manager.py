import os
import subprocess
import time

import log
from .flysight import Flysight
from .gopro import GoPro

DEFAULT_INTERVAL=10


class NotMountedError(Exception):
    """Flysight was not detected"""
    pass

@log.make_loggable
class GroupPoller(object):
    def __init__(self, pollers):
        self.pollers = pollers
        self.interval = DEFAULT_INTERVAL

    def poll_for_attach(self):
        if any(map(lambda x: x.poll_for_attach(immediate_return=True), self.pollers)):
            return True
        self.debug("No devices attached,sleeping for %ds" % self.interval)
        time.sleep(self.interval)


class AbstractPoller(object):

    device_paths = {
            'flysight': 'config.txt',
            'gopro': 'DCIM',
            }

    def __init__(self, name, ty):
        self.interval = DEFAULT_INTERVAL
        self.ty = ty
        self.name = name

    def poll_for_attach(self, already_attached=False, immediate_return=None):
        path = self.device_paths[self.ty]

        if already_attached:
            while self.device_attached(path):
                self.debug("%s still attached, waiting for disconnect" % self.ty)
                time.sleep(self.interval * 30)
            self.debug("%s disconnected" % self.ty)
        while not self.device_attached(path):
            if immediate_return:
                self.debug("%s does not exist" %
                        (self.name))
                return False
            else:
                self.debug("%s does not exist, sleeping for %ds" %
                        (self.name, self.interval))
                time.sleep(self.interval)
        return True

    def raise_unless_attached(self):
        path = self.device_paths[self.ty]

        if not self.device_attached(path):
            log.fatal("%s is not mounted" % self.ty)

    def mount(self):
        raise NotImplementedError

    def device_class(self):
        return {
            'flysight': Flysight,
            'gopro': GoPro,
        }[self.ty]


@log.make_loggable
class DirectoryPoller(AbstractPoller):
    def __init__(self, name, path, ty):
        self.path = path
        super(DirectoryPoller, self).__init__(name, ty)

    def device_attached(self, path):
        return os.path.exists(os.path.join(self.path, path))

    def mount(self, _):
        return self.device_class()(self.name, self.path)


@log.make_loggable
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
        self.info("Mounted %s on %s" % (self._flysight_path(), path))
        return self.device_class()(self.name, self.path)
