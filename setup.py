#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

"""
Package information for flysight-manager package.
"""

from setuptools import setup
import unittest

VERSION = '0.0.0'

requires = [
    'dropbox',
    'toml',
    'PyVimeo',
]

def test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    return test_suite

setup(
        name='flysight_manager',
        description="Tool for managing flysight data",
        long_description=open('README.md').read(),
        url="https://github.com/richo/flysight-manager",
        version=VERSION,
        author="Richo Healey",
        author_email="richo@psych0tik.net",
        license="MIT",
        packages=[
            'flysight_manager',
            ],
        entry_points={
            'console_scripts': [
                'flysight-manager = flysight_manager:main',
                'gopro-manager = flysight_manager.gopro_manager:main',
                ],
            },
        install_requires=requires,
        test_suite='setup.test_suite',
        )
