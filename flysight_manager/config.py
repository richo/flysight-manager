import sys
if sys.version_info.major == 2:
    import ConfigParser as configparser
else:
    import configparser

import log

from .uploader import DropboxUploader

SECT = 'flysight-manager'


class ConfigError(Exception):
    pass


class Configuration(object):
    """Stub class to be replaced by a real configuration system"""

    defaults = {
        'mountpoint': None,
        'storage_backend': 'dropbox',
        'dropbox_token': None,
    }

    CONFIG_FILE = 'flysight-manager.ini'

    def __init__(self):
        cfg = configparser.RawConfigParser(self.defaults)
        log.info("Loading config from %s" % self.CONFIG_FILE)
        cfg.read((self.CONFIG_FILE),)
        self.load_config(cfg)

        self._uploader = None

    def load_config(self, cfg):
        """Validate the configuration"""
        get = lambda x: cfg.get(SECT, x)

        mountpoint = get('mountpoint')
        if mountpoint is None:
            raise ConfigError("mountpoint is not set")
        self.mountpoint = mountpoint

        backend = get('storage_backend')
        if backend == 'dropbox':
            self.storage_backend = 'dropbox'
            self.load_dropbox_opts(cfg)
        else:
            raise ConfigError("Unknown storage_backend: %s" % backend)

    def load_dropbox_opts(self, cfg):
        get = lambda x: cfg.get(SECT, x)
        self.dropbox_token = get('dropbox_token')

    @property
    def flysight_mountpoint(self):
        return self.mountpoint

    @property
    def uploader(self):
        if not self._uploader:
            if self.storage_backend == 'dropbox':
                self._uploader = DropboxUploader(self.dropbox_token)
            else:
                raise ConfigError('Unknown storage backend: %s' % self.storage_backend)
        return self._uploader

    def update_with_args(self, args):
        if args.mountpoint:
            log.debug("Setting mountpoint to %s from args" % self.mountpoint)
            self.mountpoint = args.mountpoint
