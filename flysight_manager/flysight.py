import os
import re

from collections import namedtuple


Flight = namedtuple('Flight', ['fs_path',  # Path to find this flight on disk
                               'raw_path',  # Upload path for the raw data
                               'processed_path',  # TODO: Post processed data
                               ])


class Flysight(object):
    DATE_RE = re.compile('(?P<year>\d{2})-(?P<month>\d{2})-(?P<day>\d{2})')

    def __init__(self, path):
        self.path = path
        # Assert that we're really a flysight
        assert os.path.exists("%s/config.txt" % self.path), \
            "Specified path isn't obviously a flysight"

    def dates(self):
        dirs = os.listdir(self.path)
        dates = filter(self.DATE_RE.match, dirs)
        return dates

    def files(self, date):
        files = os.listdir(os.path.join(self.path, date))
        return files

    def flights(self):
        for date in self.dates():
            for filename in self.files(date):
                yield Flight(
                    os.path.join(self.path, date, filename),
                    os.path.join('/', date, 'raw', filename),
                    os.path.join('/', date, 'post', filename),
                )
