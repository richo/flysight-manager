import re
import time
from itertools import chain, imap
import argparse

import flysight_manager.log as log
from flysight_manager.config import Configuration, get_poller

import dropbox.files
from dropbox.files import FileMetadata, FolderMetadata, RelocationPath

def get_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('year', action='store', type=int,
                        help="Two digit year to archive")

    return parser

def get_root_contents(db):
    res = db.files_list_folder('')
    while True:
        for f in res.entries:
            yield f
        if not res.has_more:
            break
        res = db.files_list_folder_continue(res.cursor)

def get_files(db, folder, recursive):
    res = db.files_list_folder(folder, recursive=recursive)
    while True:
        for f in res.entries:
            yield f
        if not res.has_more or True:
            break
        res = db.files_list_folder_continue(res.cursor)

def recursively_delete_if_empty(db, path):
    """Attempts to delete `path` if empty, first recursively deleting any empty
    directories under `path`

    Attempts to delete non-empty directories can, but are not guaranteed to
    delete empty directories under them before failing.

    @return bool True if directory is empty and was deleted, False otherwise
    """
    for md in get_files(db, path, recursive=False):
        if isinstance(md, FileMetadata):
# This is a file, we're not empty
            log.info("Found a file at %s, bailing" % md.path_lower)
            return False
        elif isinstance(md, FolderMetadata):
            log.info("Attempting to clean out %s" % md.path_lower)
            if not recursively_delete_if_empty(db, md.path_lower):
                return False
        else:
            raise("What even is a %s" % repr(md))
    log.warn("%s is empty, deleting" % path)
    db.files_delete(path)
    return True

def main():
    cfg = Configuration()
    args = get_argparser().parse_args()
    if args.year > 100:
        raise "Not sure what to do about a year >2100"

    year_re = re.compile("^%02d-\\d\\d-\\d\\d$" % args.year)
    output_year = "20%02d" % args.year

    log.info("Archiving matches for %s into /%s" % (year_re.pattern, output_year))

    batch = []

# Uh, maybe we shouldn't do this?
    db = cfg.uploader.dropbox

    matches = filter(lambda f: year_re.match(f.name), get_root_contents(db))
    for md in chain.from_iterable(imap(lambda m: get_files(db, m.path_lower, recursive=True), matches)):
        if isinstance(md, FileMetadata):
            log.info("enqueuing %s to be archived" % md.path_lower)
            batch.append(RelocationPath(md.path_lower, "/%s%s" % (output_year, md.path_lower)))
        elif isinstance(md, FolderMetadata):
            pass
        else:
            raise("What even is a %s" % repr(md))
    log.info("Created batch job with %d entries" % len(batch))
    res = db.files_move_batch(batch)

    if not res.is_async_job_id():
        log.info("Done!")
        return
    job = res.get_async_job_id()

    status = db.files_move_batch_check(res.get_async_job_id())
    while status.is_in_progress():
        log.info("Waiting for migration to complete..")
        time.sleep(1)
        status = db.files_move_batch_check(res.get_async_job_id())
    if status.is_complete():
        log.info("Migration complete!")
    else:
        log.info("Migration failed :(")
        return

    for md in matches:
        log.info("Attempting to remove %s" % md.path_lower)
        recursively_delete_if_empty(db, md.path_lower)

if __name__ == '__main__':
    main()
