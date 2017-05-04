class UploadQueueEntry(object):
    def __init__(self, physical_path, logical_path):
        self.physical_path = physical_path


class UploadDirectory(list):
    def __init__(self, name):
        self.name = name
        super(UploadDirectory, self).__init__(self)


class UploadQueue(object):
    def __init__(self):
        pass

    def get_directory(self, d):
        if d not in self.directories:
            self.directories = UploadDirectory(d)
        return self.directories[d]

    def get_directories(self):
        return self.directories
