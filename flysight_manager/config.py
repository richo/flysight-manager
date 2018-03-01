import sys
import toml

import log

from .uploader import DropboxUploader
from .processors.gswoop import gSwoopProcessor
from .file_manager import DirectoryPoller, VolumePoller

SECT = 'flysight-manager'


class ConfigError(Exception):
    pass


class FlysightConfig(object):
    pass

class DropboxConfig(object):
    pass

class VimeoConfig(object):
    pass

class YoutubeConfig(object):
    pass

class CameraConfig(object):
    def __init__(self, name, cfg):
        self._name = name
        self._mountpoint = cfg["mountpoint"]
        self._uuid = cfg["uuid"]

    @property
    def mountpoint(self):
        return self._mountpoint

    @property
    def uuid(self):
        return self._uuid


class GoProConfig(object):
    def __init__(self):
        self._cameras = {}

    def add_camera(self, name, config):
        self._cameras[name] = CameraConfig(name, config)

    def cameras(self):
        return self._cameras


class GswoopConfig(object):
    pass


def get_poller(ty):
    if ty == 'flysight':
        get_sect = lambda cfg: cfg.flysight_cfg
    elif ty == 'gopro':
        get_sect = lambda cfg: cfg
    else:
        raise "Unknown ty: %s" % (repr(ty))

    platform = sys.platform
    if platform.startswith('linux'):
        return lambda name, cfg: VolumePoller(name, get_sect(cfg).uuid, ty)
    elif platform == 'darwin':
        return lambda name, cfg: DirectoryPoller(name, get_sect(cfg).mountpoint, ty)
    else:
        raise 'Unknown platform: %s' % (repr(platform))


class Configuration(object):
    """Stub class to be replaced by a real configuration system"""

    CONFIG_FILE = 'flysight-manager.ini'

    def __init__(self):
        self.flysight_enabled = False
        self.gopro_enabled = False
        self.gswoop_enabled = False
        self.vimeo_enabled = False
        self.youtube_enabled = False
        self.noop = False
        self.preserve = False

        self.processors = []

        log.info("Loading config from %s" % self.CONFIG_FILE)
        cfg = toml.load(open(self.CONFIG_FILE, 'rb'))
        self.load_config(cfg)

        self._uploader = None
        if self.gswoop_enabled:
            log.info("Enabling gswoop processor")
            self.processors.append("gswoop")

    def load_config(self, cfg):
        """Validate the configuration"""
        get = lambda x: cfg[SECT][x]
        # TODO: Confirm how this handles bools
        enabled = lambda x: cfg[x]["enabled"]

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

        if enabled("vimeo"):
            self.vimeo_enabled = True
            self.vimeo_cfg = self.load_vimeo_opts(cfg)

        if enabled("youtube"):
            self.youtube_enabled = True
            self.youtube_cfg = self.load_youtube_opts(cfg)

    def load_dropbox_opts(self, cfg):
        get = lambda x: cfg["dropbox"][x]
        _cfg = DropboxConfig()
        _cfg.token = get("token")
        return _cfg

    def load_vimeo_opts(self, cfg):
        get = lambda x: cfg["vimeo"][x]
        _cfg = VimeoConfig()
        _cfg.token = get("token")
        return _cfg

    def load_youtube_opts(self, cfg):
        get = lambda x: cfg["youtube"][x]
        _cfg = VimeoConfig()
        _cfg.access_token = get("access_token")
        _cfg.client_id = get("client_id")
        _cfg.client_secret = get("client_secret")
        _cfg.refresh_token = get("refresh_token")
        _cfg.token_uri = get("token_uri")
        return _cfg

    def load_gopro_opts(self, cfg):
        _cfg = GoProConfig()
# Extract the enabled key, then pray that anything else is a camera
        for k, v in cfg["gopro"].items():
            if isinstance(v, dict):
                _cfg.add_camera(k, v)
        return _cfg

    def load_flysight_opts(self, cfg):
        get = lambda x: cfg["flysight"][x]
        _cfg = FlysightConfig()
        _cfg.mountpoint = get("mountpoint")
        _cfg.uuid = get("uuid")
        return _cfg

    def load_gswoop_opts(self, cfg):
        get = lambda x: cfg["gswoop"][x]
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
        if args.preserve:
            log.debug("Setting preserve flag")
            self.preserve = args.preserve
