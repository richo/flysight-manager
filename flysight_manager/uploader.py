from dropbox import Dropbox
from dropbox.files import WriteMode

import log


class Uploader(object):
    pass


class DropboxUploader(Uploader):
    def __init__(self, token):
        self.token = token
        self.dropbox = Dropbox(self.token)
        self.mode = WriteMode('overwrite')
        super(DropboxUploader, self).__init__()

    def upload(self, fh, path):
        log.info("[dropbox] Uploading to %s" % path)
        self.dropbox.files_upload(fh, path, mode=self.mode)
