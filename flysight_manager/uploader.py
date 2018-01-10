import os
import sys
from dropbox import Dropbox

import dropbox.files
from dropbox.files import WriteMode

import log

CHUNK_SIZE = 4 * 1024 * 1024


def human_readable_size(size):
    multiplier = 1
    if size < 1024:
        return "%d" % size
    for unit in ('k', 'm', 'g', 't'):
        multiplier *= 1024
        if size < 1024 * multiplier:
            return "%d%s" % (float(size) / multiplier, unit)
    return "%dt" % (float(size) / multiplier)


class Uploader(object):
    pass


class DropboxUploader(Uploader):
    def __init__(self, token, noop, preserve):
        self.token = token
        self.noop = noop
        self.preserve = preserve
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
                if self.noop:
                    log.info("Not removing %s, noop specified" % (entry.physical_path))
                elif self.preserve:
                    log.info("Not removing %s, preserve specified" % (entry.physical_path))
                else:
                    log.info("Removing %s" % entry.physical_path)
                    os.unlink(entry.physical_path)


    def upload_small_file(self, fs_path, logical_path):
        return self.dropbox.files_upload(
                open(fs_path, 'rb'),
                logical_path,
                mode=self.mode
                )

    def upload_large_file(self, fs_path, logical_path):
        size = os.stat(fs_path).st_size

        def _next_char():
            while True:
                for i in '-\\|/':
                    yield i
        next_char_iter = _next_char()
        next_char = lambda: next_char_iter.next()


        def write_status_line(msg):
            sys.stdout.write("\33[2K\r")
            sys.stdout.flush()
            sys.stdout.write("[%s] " % (next_char()))
            sys.stdout.write(msg)
            sys.stdout.flush()

        with open(fs_path, 'rb') as fh:
            log.info("[dropbox] Starting large upload of %s bytes" % (human_readable_size(size)))
            upload_session_start_result = self.dropbox.files_upload_session_start(fh.read(CHUNK_SIZE))
            cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                       offset=fh.tell())
            commit = dropbox.files.CommitInfo(path=logical_path)

            while fh.tell() < size:
                if ((size - fh.tell()) <= CHUNK_SIZE):
                    if sys.stdout.isatty():
                        write_status_line("Uploading last chunk\n")
                    print self.dropbox.files_upload_session_finish(fh.read(CHUNK_SIZE),
                                                    cursor,
                                                    commit)
                else:
                    if sys.stdout.isatty():
                        progress = int((float(cursor.offset) / float(size)) * 100)
                        write_status_line("Uploading %s bytes from %s (%d%%)" % (human_readable_size(CHUNK_SIZE), human_readable_size(cursor.offset), progress))
                    self.dropbox.files_upload_session_append(fh.read(CHUNK_SIZE),
                                                    cursor.session_id,
                                                    cursor.offset)
                    cursor.offset = fh.tell()
                    # log.info("[dropbox] Uploaded to byte %x" % (fh.tell()))
