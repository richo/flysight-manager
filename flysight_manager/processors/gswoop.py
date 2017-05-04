import log
import subprocess

from flysight_manager.upload_queue import UploadQueueEntry


class gSwoopProcessor(object):
    def __init__(self, cfg):
        self.cfg = cfg

    def process(self, physical_path, upload_queue):
        self._gswoop(['-i', physical_path])
        queue = upload_queue.get_directory('gswoop')
        queue.append(physical_path, physical_path)
        for i in self._all_gswoop_products(physical_path):
            queue.append(UploadQueueEntry(i, i))

    def _gswoop(self, args):
        args = [self.cfg.gswoop_cfg.binary] + args
        log.info("[gswoop] %s" % repr(args))
        subprocess.check_call([self.gswoop_binary] + args)

    @staticmethod
    def _all_gswoop_products(filename):
        trimmed = filename[:-3]
        return [trimmed + i for i in ['kml', 'pdf', 'txt']]
