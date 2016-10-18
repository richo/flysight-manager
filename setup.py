#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

"""
Package information for flysight-manager package.
"""

from setuptools import setup

VERSION = '0.0.0'

requires = [
    'dropbox',
]

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
                ],
            },
        install_requires=requires,
        )
