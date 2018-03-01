import os
import sys
import contextlib
import time
import datetime
import threading
import Queue
from dropbox import Dropbox
import requests
from tusclient import client as tusclient
import json

import dropbox.files
from dropbox.files import WriteMode

import log

CHUNK_SIZE = 4 * 1024 * 1024
STATUS_WIDTH = 60
VIMEO_API_BASE = "https://api.vimeo.com"

class VimeoUploadFailed(BaseException):
    pass
class YoutubeUploadFailed(BaseException):
    pass

class StatusPrinter(threading.Thread):
    def __init__(self, start_time, size, write_line):
        self.queue = Queue.Queue()
        self.start_time = start_time
        self.size = size
        self.write_line = write_line

        super(StatusPrinter, self).__init__()

        self.daemon = True

    def run(self):
        log.debug("[printer] Starting printer thread")
        msg = None
        last = None
        while True:
            try:
                item = self.queue.get(block=True, timeout=1)
                if item is None:
# Let this thread die, upload is complete
                    log.debug("[printer] Got thread termination msg")
                    break

                (now, offset) = item

                progress = (float(offset) / float(self.size))
                marked = int(progress * STATUS_WIDTH)
                progress = int(progress * 100)
                remaining_time = time_left(self.size, offset, self.start_time, now)

                msg = "|%s%s| %02d%% ETA: {eta}" % (
                        "-" * (marked),
                        " " * (STATUS_WIDTH - marked),
                        progress,
                        # time_left(size, offset, self.start_time, now)
                )
                if last:
                    msg += " (%s/s)" % upload_speed(CHUNK_SIZE, now - last)

                self.write_line(msg.format(eta=human_readable_time(remaining_time)))
                last = now

            except Queue.Empty:
# Update ETA, write line
                if msg and remaining_time:
                    remaining_time -= 1
# This is worthwhile even if the message hasn't changed, because of the spinner
                if msg:
                    self.write_line(msg.format(eta=human_readable_time(remaining_time)))
        log.debug("StatusWriter is terminating")


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

def human_readable_time(seconds):
# Super hacky, but we want to support handing numerics around elsewhere
    if seconds is None:
        return "unknown"

    out = ""
    if seconds > 60:
        mins, seconds = divmod(seconds, 60)
        if mins > 60:
            hours, mins = divmod(mins, 60)
            out += "%dh" % hours
        out += "%dm" % mins
    out += "%ds" % seconds
    return out

def time_left(size, uploaded, start_time, now):
    dt = float(now) - float(start_time)
    if dt < 1:
# Unlikely to have useful data extrapolating from less than a second
        return None
    ds = float(uploaded)

    speed = dt / ds
    return (size - ds) * speed


def upload_speed(byts, dt):
    return human_readable_size(float(byts) / dt)

class Uploader(object):
    pass

class YoutubeUploader(Uploader):
    def __init__(self, cfg, noop):
# This is sort of shitty, but the dependencies for this thing are the fucking worst, so we don't try to get em till we need em
        self.cfg = cfg
        self.noop = noop

    def _get_authenticated_service(self):
        from googleapiclient.discovery import build
        from oauth2client.client import AccessTokenCredentials, GoogleCredentials
        API_SERVICE_NAME = 'youtube'
        API_VERSION = 'v3'

        # credentials = AccessTokenCredentials(self.token, 'flysight-manager/0.0.0')
        credentials = GoogleCredentials(
                self.cfg.access_token,
                self.cfg.client_id,
                self.cfg.client_secret,
                self.cfg.refresh_token,
                datetime.datetime(2018, 3, 1, 1, 37, 8, 846706), # lol
                self.cfg.token_uri,
                'flysight-manager/0.0.0')

        log.debug("[youtube] creating service object")
        return build(API_SERVICE_NAME, API_VERSION, credentials = credentials)

    def upload(self, fs_path, logical_path):
        """The logical path abstraction is a bit goofy"""
        return self.upload_file(fs_path, logical_path, logical_path)

    def upload_file(self, filename, title, description):
        size = os.stat(filename).st_size
        from googleapiclient.http import MediaFileUpload
        youtube = self._get_authenticated_service()

        log.info("[youtube] Uploading %s bytes from %s as name: %s description: %s" % (human_readable_size(size), filename, title, description))

        body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": [],
                    "categoryId": "17", # sports, why not
                    },
                "status": {
                    "privacyStatus": "unlisted",
                    }
                }

        # Call the API's videos.insert method to create and upload the video.
        request = youtube.videos().insert(
                  part=','.join(body.keys()),
                  body=body,
                  media_body=MediaFileUpload(filename, chunksize=CHUNK_SIZE, resumable=True)
                  )
        log.debug("[youtube] Created insert object")

        start = time.time()
        try:
            with status_line() as write_status_line:
                if sys.stdout.isatty():
                    printer = StatusPrinter(start, size, write_status_line)
                    printer.start()
                response = None
                while response is None:
                    status, response = request.next_chunk()
                    if sys.stdout.isatty():
                        printer.queue.put((time.time(), request.resumable_progress))
                    if response is not None:
                        printer.queue.put(None)
                        printer.join()
                        if 'id' in response:
                            write_status_line('[youtube] Video id "%s" was successfully uploaded.\n' % response['id'])
                        else:
                            write_status_line('[youtube] The upload failed with an unexpected response: %s\n' % response)
                            raise YoutubeUploadFailed(str(response))
        finally:
# TODO Turns out YT also does the "partial upload" thing
            printer.queue.put(None)
        log.info("[youtube] Uploaded {title} in {t}"
                    .format(
                        title=title,
                        t = human_readable_time(int(time.time() - start))))

class VimeoUploader(Uploader):
    def __init__(self, token, noop):
        self.token = token
        self.noop = noop

    def _authorization_header(self):
        return "bearer %s" % self.token

    def _post(self, url, payload):
        headers = {
                    "Authorization": self._authorization_header(),
                    "Content-Type": "application/json",
                    }
        resp = requests.post(VIMEO_API_BASE + url,
                headers = headers,
                data = json.dumps(payload),
                )
        return resp

    def _delete(self, url):
        headers = {
                    "Authorization": self._authorization_header(),
                    }
        resp = requests.delete(VIMEO_API_BASE + url,
                headers = headers,
                )
        return resp

    def upload(self, fs_path, logical_path):
        """The logical path abstraction is a bit goofy"""
        return self.upload_file(fs_path, logical_path, logical_path)

    def upload_file(self, filename, name, description):
        printer = None
        size = os.stat(filename).st_size
        log.info("[vimeo] Uploading %s bytes from %s as name: %s description: %s" % (human_readable_size(size), filename, name, description))
        resp = self._post("/me/videos", {
            "upload": {"approach": "tus", "size": size},
            "name": name,
            "description": description,
            "privacy": {
                "download": "false",
                "view": "unlisted",
                }
            })

        data = resp.json()
        video_uri = data['uri']

        def delete_invalid_video(error):
            if printer:
                printer.queue.put(None)
                printer.join()
            log.warn("[vimeo] video upload looks broken, deleting incomplete video")
            self._delete(video_uri)
# Guarantee we don't accidentally continue
            raise VimeoUploadFailed(error)

        if resp.status_code != 200:
            delete_invalid_video(resp.text)

        upload_link = data["upload"]["upload_link"]
        log.debug("[vimeo] Creating client aimed at %s" % upload_link)

# Shamelessly stolen from vimeo.py
        client = tusclient.TusClient(upload_link)

        start = time.time()
        try:
            with open(filename) as fh, status_line() as write_status_line:
                if sys.stdout.isatty():
                    printer = StatusPrinter(start, size, write_status_line)
                    printer.start()
                uploader = client.uploader(file_stream=fh, url=upload_link, chunk_size=CHUNK_SIZE)
                while uploader.offset < uploader.stop_at:
                    if sys.stdout.isatty():
                        printer.queue.put((time.time(), uploader.offset))
                    uploader.upload_chunk()
                printer.queue.put(None)
                printer.join()
                write_status_line("[vimeo] Uploaded {name} in {t}\n"
                        .format(
                            name=name,
                            t = human_readable_time(int(time.time() - start))))
        except Exception as e:
            printer.queue.put(None)
            delete_invalid_video(str(e))
        finally:
            printer.queue.put(None)


class DropboxUploader(Uploader):
    def __init__(self, token, noop):
        self.token = token
        self.noop = noop
        self.dropbox = Dropbox(self.token)
        self.mode = WriteMode('overwrite')
        super(DropboxUploader, self).__init__()

    def upload(self, fs_path, logical_path):
        size = os.stat(fs_path).st_size

        log.info("[dropbox] Uploading %s bytes from %s" % ((human_readable_size(size)), fs_path))
        with open(fs_path, 'rb') as fh, status_line() as write_status_line:
            last = None
            start = time.time()
            if sys.stdout.isatty():
                printer = StatusPrinter(start, size, write_status_line)
                printer.start()
# Only upload a few bytes to start
            upload_session_start_result = self.dropbox.files_upload_session_start(fh.read(64))
            cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                       offset=fh.tell())
            commit = dropbox.files.CommitInfo(path=logical_path)

            while fh.tell() < size:
                if ((size - fh.tell()) <= CHUNK_SIZE):
                    if sys.stdout.isatty():
                        # Close out our updater thread, then write this line out.
                        printer.queue.put(None)
                        write_status_line("[dropbox] Uploading last chunk (%s/s)\n" % upload_speed(size, time.time() - start))
                    res = self.dropbox.files_upload_session_finish(fh.read(CHUNK_SIZE),
                                                    cursor,
                                                    commit)
                    log.info("[dropbox] Uploaded {p.name} to {p.path_lower} in {t}"
                                .format(
                                    p = res,
                                    t = human_readable_time(int(time.time() - start))))
                else:
                    if sys.stdout.isatty():
                        printer.queue.put((time.time(), cursor.offset))

                    last = time.time()
                    self.dropbox.files_upload_session_append(fh.read(CHUNK_SIZE),
                                                    cursor.session_id,
                                                    cursor.offset)
                    cursor.offset = fh.tell()
