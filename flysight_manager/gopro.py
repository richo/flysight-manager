import os
import re
import subprocess
import time

import log

from collections import namedtuple


Video = namedtuple('Video', ['fs_path',  # Path to find this flight on disk
                             'upload_path',  # Upload path for the raw data
                             ])


class GoPro(object):
    VIDEO_PATH = "DCIM/100GOPRO"

    def __init__(self, path):
        # TODO load this from config
# This is good enough for now, although it's an hour off with DST
        self.offset = -28800
        self.path = path
        # Assert that we're really a flysight
        assert os.path.exists("%s/DCIM" % self.path), \
            "Specified path isn't obviously a gopro"

    def videos(self):
        video_path = os.path.join(self.path, self.VIDEO_PATH)
        files = sorted(filter(lambda x: x.endswith(".MP4"), os.listdir(video_path)))
        for f in files:
            path = os.path.join(video_path, f)
            st = os.stat(path)
# We use gmtime because we've already done kooky offset math
            timeinfo = time.gmtime(st.st_mtime + self.offset)
            date = '%02d-%02d-%02d' % (timeinfo.tm_year % 100,
                                 timeinfo.tm_mon,
                                 # Portability?
                                 timeinfo.tm_mday)
            # TODO maybe try to do something clever with time?
            logical_path = os.path.join('/', date, 'video', os.path.basename(path))
            yield Video(
                    path,
                    logical_path
            )

    def unmount(self):
        log.info("Trying to unmount %s" % self.path)
        subprocess.check_call(['sudo', 'umount', self.path])

    def __del__(self):
        try:
            log.info("Trying to unmount %s" % self.path)
            subprocess.check_call(['sudo', 'umount', self.path])
        except:
            log.warn("Error unmounting flysight, continuing")
