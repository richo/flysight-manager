import collections

class UploadQueueEntry(object):
    def __init__(self, physical_path, logical_path):
        self.physical_path = physical_path
        self.logical_path = logical_path

class UploadQueue(object):
    def __init__(self):
        self.directories = collections.defaultdict(list)
        self.uploaders = []

    def get_directory(self, d):
        return self.directories[d]

    def get_directories(self):
        return self.directories

    def add_uploader(self, uploader):
        self.uploaders.append(uploader)

    def process_queue(self, preserve=False):
        for name, directory in self.directories.items():
            log.info("processing %s" % repr(name))
            for entry, i in enumerate(directory):
                logical_path = os.path.join(name, entry.logical_path)
                for uploader in self.uploaders:
                    uploader.upload(entry.physical_path, logical_path)
                if not preserve:
                    log.info("Removing %s" % entry.physical_path)
                    os.unlink(entry.physical_path)
                else:
                    log.info("Not removing %s, preserve specified" % entry.physical_path)


