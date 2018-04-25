#!/usr/bin/env python

import unittest
from flysight_manager import config

# omg, what even did I do here
class TestableConfiguration(config.Configuration):
    CONFIG_FILE = 'flysight-manager.ini.example'


class TestConfigParser(unittest.TestCase):
    def test_config(self):
        cfg = TestableConfiguration()
