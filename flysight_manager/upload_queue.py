import os
import collections
import log

@log.make_loggable
class UploadQueueEntry(object):
    def __init__(self, physical_path, logical_path):
        self.physical_path = physical_path
        self.logical_path = logical_path

@log.make_loggable
class UploadQueue(object):
    def __init__(self):
        self.directories = collections.defaultdict(list)

        self.upload_notifiers = []
        self.completion_notifiers = []

    def get_directory(self, d):
        return self.directories[d]

    def get_directories(self):
        return self.directories

    def notify_on_completion(self, notifier):
        self.completion_notifiers.append(notifier)

    def notify_on_upload(self, notifier):
        self.upload_notifiers.append(notifier)

    def process_queue(self, uploaders, preserve=False, report=None):
        for name, directory in self.directories.items():
            self.info("processing %s" % repr(name))
            for i, entry in enumerate(directory):
                logical_path = os.path.join(name, entry.logical_path)
                for uploader in uploaders:
                    uploader.upload(entry.physical_path, logical_path)
                    if report:
                        report.add_uploaded_file(entry.physical_path)
                    for notifier in self.upload_notifiers:
                        notifier.notify("Uploaded %s" % (entry.physical_path))
                if not preserve:
                    self.info("Removing %s" % entry.physical_path)
                    os.unlink(entry.physical_path)
                else:
                    self.info("Not removing %s, preserve specified" % entry.physical_path)
        for notifier in self.completion_notifiers:
            notifier.notify("Finished upload run")
