import os
from dropbox import Dropbox

import dropbox.files
from dropbox.files import WriteMode

import log

CHUNK_SIZE = 4 * 1024 * 1024


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
        for name, directory in queue.get_directories().items():
            log.info("[dropbox] processing %s" % repr(name))
            for entry in directory:
                logical_path = os.path.join(name, entry.logical_path)
                log.info("[dropbox] Uploading %s to %s" % (
                    entry.physical_path, logical_path))
                if not self.noop:
                    size = os.stat(entry.physical_path).st_size
                    if size > CHUNK_SIZE:
                        self.upload_large_file(entry.physical_path, logical_path)
                    else:
                        self.upload_small_file(entry.physical_path, logical_path)
                log.info("Removing %s" % entry.physical_path)
                if not self.noop:
                    os.unlink(entry.physical_path)

    def upload_small_file(self, fs_path, logical_path):
        return self.dropbox.files_upload(
                open(fs_path, 'rb'),
                logical_path,
                mode=self.mode
                )

    def upload_large_file(self, fs_path, logical_path):
        size = os.stat(fs_path).st_size
        with open(fs_path, 'rb') as fh:
            log.info("[dropbox] Starting large upload of %x bytes" % (size))
            upload_session_start_result = self.dropbox.files_upload_session_start(fh.read(CHUNK_SIZE))
            cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                       offset=fh.tell())
            commit = dropbox.files.CommitInfo(path=logical_path)

            while fh.tell() < size:
                if ((size - fh.tell()) <= CHUNK_SIZE):
                    print self.dropbox.files_upload_session_finish(fh.read(CHUNK_SIZE),
                                                    cursor,
                                                    commit)
                else:
                    self.dropbox.files_upload_session_append(fh.read(CHUNK_SIZE),
                                                    cursor.session_id,
                                                    cursor.offset)
                    cursor.offset = fh.tell()
                    # log.info("[dropbox] Uploaded to byte %x" % (fh.tell()))
