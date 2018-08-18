import os
import re
import subprocess

from flysight_manager import log
from flysight_manager.upload_queue import UploadQueueEntry


# FIXME: This is copypasted from the flysight handler
TIME_RE = re.compile('(?P<year>\d{2})-(?P<month>\d{2})-(?P<day>\d{2})/(?P<hour>\d{2})-(?P<minute>\d{2})-(?P<second>\d{2})')


@log.make_loggable
class gSwoopProcessor(object):
    def __init__(self, cfg):
        self.cfg = cfg

    def process(self, flight, upload_queue):
        self._gswoop(['-i', flight.fs_path])
        queue = upload_queue.get_directory('gswoop')
        for i, extension in self._all_gswoop_products(flight.fs_path):
            time = TIME_RE.search(flight.fs_path)
            year, month, day, hour, minute, second = time.groups()
            logical_path = os.path.join(
                '/', '%s-%s-%s' % (year, month, day),
                'gswoop', '%s-%s-%s.%s' % (hour, minute, second, extension)
            )

            queue.append(UploadQueueEntry(i, logical_path))

    def _gswoop(self, args):
        args = [self.cfg.gswoop_cfg.binary] + args
        self.info("[gswoop] %s" % repr(args))
        if not self.cfg.noop:
            subprocess.check_call(args)

    @staticmethod
    def _all_gswoop_products(filename):
        trimmed = filename[:-3]
        return [(trimmed + i, i) for i in ['kml', 'pdf', 'txt']]
