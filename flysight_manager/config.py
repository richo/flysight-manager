import sys
if sys.version_info.major == 2:
    import ConfigParser as configparser
else:
    import configparser

import log

from .uploader import DropboxUploader
from .processors.gswoop import gSwoopProcessor

SECT = 'flysight-manager'


class ConfigError(Exception):
    pass


class FlysightConfig(object):
    pass


class DropboxConfig(object):
    pass


class GoProConfig(object):
    pass


class GswoopConfig(object):
    pass


class Configuration(object):
    """Stub class to be replaced by a real configuration system"""

    CONFIG_FILE = 'flysight-manager.ini'

    def __init__(self):
        self.flysight_enabled = False
        self.gopro_enabled = False
        self.gswoop_enabled = False

        self.processors = []

        cfg = configparser.RawConfigParser()
        log.info("Loading config from %s" % self.CONFIG_FILE)
        cfg.read((self.CONFIG_FILE),)
        self.load_config(cfg)

        self._uploader = None
        if self.gswoop_enabled:
            log.info("Enabling gswoop processor")
            self.processors.append("gswoop")

    def load_config(self, cfg):
        """Validate the configuration"""
        get = lambda x: cfg.get(SECT, x)
        # TODO: Confirm how this handles bools
        enabled = lambda x: cfg.getboolean(x, "enabled")

        backend = get('storage_backend')
        if backend == 'dropbox':
            self.storage_backend = 'dropbox'
            self.dropbox_cfg = self.load_dropbox_opts(cfg)
        else:
            raise ConfigError("Unknown storage_backend: %s" % backend)

        if enabled("flysight"):
            self.flysight_enabled = True
            self.flysight_cfg = self.load_flysight_opts(cfg)

        if enabled("gopro"):
            self.gopro_enabled = True
            self.gopro_cfg = self.load_gopro_opts(cfg)

        if enabled("gswoop"):
            self.gswoop_enabled = True
            self.gswoop_cfg = self.load_gswoop_opts(cfg)

    def load_dropbox_opts(self, cfg):
        get = lambda x: cfg.get("dropbox", x)
        _cfg = DropboxConfig()
        _cfg.token = get("token")
        return _cfg

    def load_gopro_opts(self, cfg):
        get = lambda x: cfg.get("gopro", x)
        _cfg = GoProConfig()
        _cfg.mountpoint = get("mountpoint")
        _cfg.uuid = get("uuid")
        return _cfg

    def load_flysight_opts(self, cfg):
        get = lambda x: cfg.get("flysight", x)
        _cfg = FlysightConfig()
        _cfg.mountpoint = get("mountpoint")
        _cfg.uuid = get("uuid")
        return _cfg

    def load_gswoop_opts(self, cfg):
        get = lambda x: cfg.get("gswoop", x)
        _cfg = GswoopConfig()
        _cfg.binary = get("binary")
        return _cfg

    @property
    def uploader(self):
        if not self._uploader:
            if self.storage_backend == 'dropbox':
                self._uploader = DropboxUploader(self.dropbox_cfg.token, self.noop)
            else:
                raise ConfigError('Unknown storage backend: %s' % self.storage_backend)
        return self._uploader

    def update_with_args(self, args):
        if args.noop:
            log.debug("Setting noop flag")
            self.noop = args.noop
