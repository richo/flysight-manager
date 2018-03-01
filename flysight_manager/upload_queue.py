import os
import collections
import log

class UploadQueueEntry(object):
    def __init__(self, physical_path, logical_path):
        self.physical_path = physical_path
        self.logical_path = logical_path

class UploadQueue(object):
    def __init__(self):
        self.directories = collections.defaultdict(list)

    def get_directory(self, d):
        return self.directories[d]

    def get_directories(self):
        return self.directories

    def process_queue(self, uploaders, preserve=False):
        for name, directory in self.directories.items():
            log.info("[queue] processing %s" % repr(name))
            for i, entry in enumerate(directory):
                logical_path = os.path.join(name, entry.logical_path)
                for uploader in uploaders:
                    uploader.upload(entry.physical_path, logical_path)
                if not preserve:
                    log.info("Removing %s" % entry.physical_path)
                    os.unlink(entry.physical_path)
                else:
                    log.info("Not removing %s, preserve specified" % entry.physical_path)


