import os
import shutil
import tempfile
import unittest

from flysight import Flysight


class TestFlysight(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        target = os.path.join(self.directory, 'flysight')
        shutil.copytree('test_data', target)

        self.flysight = Flysight(target)

    def tearDown(self):
        shutil.rmtree(self.directory)

    def test_dates(self):
        self.assertEqual(['16-09-25', '16-10-08'], self.flysight.dates())


if __name__ == '__main__':
    unittest.main()
