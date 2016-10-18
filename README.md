flysight-manager
================

A tool for uploading flysight data directly to 🆃🅷🅴 🅲🅻🅾🆄🅳

At it's simplest:

* Get a dropbox token. Put it in .flysight-token
* Configure your mounter (see below)
* edit `config.ini.example` and save as `config.ini`
* Configure your system to allow whichever user you'll run this as to `sudo
  umount $mountpoint` without a password.
* Test run without arguments
* Arrange to run it with `--daemon`


# Mounting

On OSX it should be sufficient to merely tell it to look for `/Volumes/NO NAME` (or rename your flysight).

On linux you probably want to do some uuid-fstab-neckbeard shenanigans.
