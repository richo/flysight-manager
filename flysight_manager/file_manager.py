import os
import subprocess
import time

import log
from .flysight import Flysight


class NotMountedError(Exception):
    """Flysight was not detected"""
    pass


class AbstractPoller(object):
    def __init__(self):
        self.interval = 10

    def poll_for_attach(self):
        while not self._flysight_attached():
            log.debug("%s does not exist, sleeping for %ds" %
                      (self.path, self.interval))
            time.sleep(self.interval)

    def raise_unless_attached(self):
        if not self._flysight_attached():
            raise NotMountedError("Flysight is not mounted")

    def mount(self):
        raise NotImplementedError


class DirectoryPoller(AbstractPoller):
    def __init__(self, path):
        self.path = path
        super(DirectoryPoller).__init__(self)

    def _flysight_attached(self):
        return os.path.exists(os.path.join(self.path, 'config.txt'))

    def mount(self):
        return Flysight(self.path)


class VolumePoller(AbstractPoller):
    def __init__(self, uuid):
        self.uuid = uuid
        super(DirectoryPoller).__init__(self)

    def _flysight_attached(self):
        return os.path.exists(os.path.join(
            '/', 'dev', 'disk', 'by-uuid', self.uuid))

    def mount(self):
        subprocess.check_call(['sudo', 'mount', self.path])
        return Flysight(self.path)
