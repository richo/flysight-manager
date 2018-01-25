import os
import sys
import contextlib
import time
from dropbox import Dropbox

import dropbox.files
from dropbox.files import WriteMode

import log

CHUNK_SIZE = 4 * 1024 * 1024
STATUS_WIDTH = 60

@contextlib.contextmanager
def status_line():
    def _next_char():
        while True:
            for i in '-\\|/':
                yield i
    next_char_iter = _next_char()
    next_char = lambda: next_char_iter.next()
    def write_status_line(msg):
        sys.stdout.write("\33[2K\r")
        sys.stdout.write("[%s] " % (next_char()))
        sys.stdout.write(msg)
        sys.stdout.flush()
    yield write_status_line
    sys.stdout.write("\33[2K\r")
    sys.stdout.flush()

def human_readable_size(size):
    multiplier = 1
    if size < 1024:
        return "%d" % size
    for unit in ('k', 'm', 'g', 't'):
        multiplier *= 1024
        if unit != 'k' and size < multiplier * 10:
            return "%.2f%s" % (float(size) / multiplier, unit)
        if size < 1024 * multiplier:
            return "%d%s" % (float(size) / multiplier, unit)
    return "%dt" % (float(size) / multiplier)

def upload_speed(byts, dt):
    return human_readable_size(float(byts) / dt)



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
                    self.upload_large_file(entry.physical_path, logical_path)
                if self.noop:
                    log.info("Not removing %s, noop specified" % (entry.physical_path))
                elif self.preserve:
                    log.info("Not removing %s, preserve specified" % (entry.physical_path))
                else:
                    log.info("Removing %s" % entry.physical_path)
                    os.unlink(entry.physical_path)


    def upload_large_file(self, fs_path, logical_path):
        size = os.stat(fs_path).st_size

        log.info("[dropbox] Uploading %s bytes from %s" % ((human_readable_size(size)), fs_path))
        with open(fs_path, 'rb') as fh, status_line() as write_status_line:
            last = None
            start = time.time()
# Only upload a few bytes to start
            upload_session_start_result = self.dropbox.files_upload_session_start(fh.read(64))
            cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                       offset=fh.tell())
            commit = dropbox.files.CommitInfo(path=logical_path)

            while fh.tell() < size:
                if ((size - fh.tell()) <= CHUNK_SIZE):
                    if sys.stdout.isatty():
                        write_status_line("Uploading last chunk (%s/s)\n" % upload_speed(size, time.time() - start))
                    print self.dropbox.files_upload_session_finish(fh.read(CHUNK_SIZE),
                                                    cursor,
                                                    commit)
                else:
                    if sys.stdout.isatty():
                        now = time.time()
                        progress = (float(cursor.offset) / float(size))
                        marked = int(progress * STATUS_WIDTH)
                        progress = int(progress * 100)

                        msg = "|%s%s| %02d%%" % (
                                "-" * (marked),
                                " " * (STATUS_WIDTH - marked),
                                progress
                        )
                        if last:
                            msg += " (%s/s)" % upload_speed(CHUNK_SIZE, now - last)

                        write_status_line(msg)

                    last = time.time()
                    self.dropbox.files_upload_session_append(fh.read(CHUNK_SIZE),
                                                    cursor.session_id,
                                                    cursor.offset)
                    cursor.offset = fh.tell()
