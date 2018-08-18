import unittest
from flysight_manager import uploader

import flysight_manager.log
flysight_manager.log.suppress_logs()


class TestUploaderSizeFormatter(unittest.TestCase):
    def test_suffix(self):
        hrs = uploader.human_readable_size

        self.assertEqual(hrs(1000), '1000')
        self.assertEqual(hrs(1024), '1k')
        self.assertEqual(hrs(1024 * 1024), '1.00m')
        self.assertEqual(hrs(1044 * 1024), '1.02m')
        self.assertEqual(hrs(5.5 * 1024 * 1024), '5.50m')
        self.assertEqual(hrs(1024 * 100 + 100), '100k')
        self.assertEqual(hrs(5), '5')
        self.assertEqual(hrs(2000), '1k')
        self.assertEqual(hrs(1024 * 1024 * 1024 * 1024 * 1024), '1024t')
