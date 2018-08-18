#!/usr/bin/env python

import unittest
from flysight_manager import config

import flysight_manager.log
flysight_manager.log.suppress_logs()

class TestableConfiguration(config.Configuration):
    CONFIG_FILE = 'flysight-manager.ini.example'


class TestConfigParser(unittest.TestCase):
    def test_config(self):
        cfg = TestableConfiguration()
