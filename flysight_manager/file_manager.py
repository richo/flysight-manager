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
        super(DirectoryPoller, self).__init__()

    def _flysight_attached(self):
        return os.path.exists(os.path.join(self.path, 'config.txt'))

    def mount(self):
        return Flysight(self.path)


class VolumePoller(AbstractPoller):
# TODO Make this unmount on exit always
    def __init__(self, uuid):
        self.uuid = uuid
        super(VolumePoller, self).__init__()

    def _flysight_path(self):
        return os.path.join('/', 'dev', 'disk', 'by-uuid', self.uuid)
    def _flysight_attached(self):
        return os.path.exists(self._flysight_path())

    def mount(self, path):
        subprocess.check_call(['sudo', 'mount', self._flysight_path(), path])
        log.info("Mounted %s on %s" % (self._flysight_path(), path))
        return Flysight(path)
