import os


class Configuration(object):
    """Stub class to be replaced by a real configuration system"""
    def __init__(self):
        pass

    @property
    def flysight_mountpoint(self):
        return "/tmp/flysight"
        return "/Volumes/NO_NAME"

    @property
    def storage_backend(self):
        return "dropbox"

    def dropbox_credentials(self):
        """returns a tuple of dropbox credentials"""
        return open('.flysight-token').read().strip()

    def dropbox_target(self):
        """returns the directory to sync to in dropbox"""
        return "flysight"

    def update_with_args(self, args):
        # TODO
        pass
