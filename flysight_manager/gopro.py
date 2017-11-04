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
    # TODO They use other \d\d\dGOPRO directories
    VIDEO_PATH_REGEX = re.compile(r"\d\d\dGOPRO")

    def __init__(self, path):
        # TODO load this from config
# This is good enough for now, although it's an hour off with DST
        self.offset = -28800
        self.path = path
        # Assert that we're really a flysight
        assert os.path.exists("%s/DCIM" % self.path), \
            "Specified path isn't obviously a gopro"

    def video_dirs(self):
        dcim = os.path.join(self.path, "DCIM")
        paths = filter(self.VIDEO_PATH_REGEX.match, os.listdir(dcim))
        return map(lambda x: os.path.join(dcim, x), paths)

    def video_files(self):
        for d in self.video_dirs():
            for f in os.listdir(d):
                yield os.path.join(d, f)

    def videos(self):
        files = sorted(
                filter(lambda x: not os.path.basename(x).startswith("._"),
                filter(lambda x: x.endswith(".MP4"),
                self.video_files()
                )))
        for path in files:
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
        #subprocess.check_call(['sudo', 'umount', self.path])

    def __del__(self):
        try:
            log.info("Trying to unmount %s" % self.path)
            #subprocess.check_call(['sudo', 'umount', self.path])
        except:
            log.warn("Error unmounting flysight, continuing")
