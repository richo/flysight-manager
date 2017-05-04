import collections

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
