import os
from dropbox import Dropbox

from dropbox.files import WriteMode

import log


class Uploader(object):
    pass


class DropboxUploader(Uploader):
    def __init__(self, token, noop):
        self.token = token
        self.noop = noop
        self.dropbox = Dropbox(self.token)
        self.mode = WriteMode('overwrite')
        super(DropboxUploader, self).__init__()

    def handle_queue(self, queue):
        for directory in queue.get_directories():
            for entry in directory.get_entries():
                logical_path = os.path.join(directory.name, entry.logical_path)
                log.info("[dropbox] Uploading %s to %s" % (
                    entry.physical_path, logical_path))
                if not self.noop:
                    self.dropbox.files_upload(
                        open(entry.physical_path, 'rb'),
                        logical_path,
                        mode=self.mode
                        )
                log.info("Removing %s" % entry.physical_path)
                if not self.noop:
                    os.unlink(entry.physical_path)
