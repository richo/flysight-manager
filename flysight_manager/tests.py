import os
import shutil
import tempfile
import unittest

from flysight import Flysight
from processors.gswoop import gSwoopProcessor


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


class TestgSwoop(unittest.TestCase):
    def test_all_filenames(self):
        filename = "13-58-13.CSV"
        products = gSwoopProcessor._all_gswoop_products(filename)
        self.assertEqual(len(products), 3)
        self.assertIn("13-58-13.kml", products)
        self.assertIn("13-58-13.pdf", products)
        self.assertIn("13-58-13.txt", products)


if __name__ == '__main__':
    unittest.main()
