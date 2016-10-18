import os
import subprocess
import time

import log


class NotMountedError(Exception):
    """Flysight was not detected"""
    pass


class MountPoller(object):
    def __init__(self, path):
        self.path = path
        self.interval = 10

    def _flysight_attached(self):
        return os.path.exists(os.path.join(self.path, 'config.txt'))

    def poll_for_attach(self):
        while not self._flysight_attached():
            log.debug("%s does not exist, sleeping for %ds" %
                      (self.path, self.interval))
            time.sleep(self.interval)

    def raise_unless_attached(self):
        if not self._flysight_attached():
            raise NotMountedError("Flysight is not mounted")


class Unmounter(object):
    def __init__(self, path):
        self.path = path

    def unmount(self):
        log.info("Trying to unmount %s" % self.path)
        subprocess.check_call(['sudo', 'umount', self.path])
