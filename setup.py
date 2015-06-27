#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from setuptools import setup, find_packages

import sys
if sys.version_info < (2, 6):
    print("THIS MODULE REQUIRES PYTHON 2.6 OR LATER. YOU ARE CURRENTLY USING PYTHON " + sys.version)
    sys.exit(1)

import PyBaiduYuyin

setup(
    name="PyBaiduYuyin",
    version=PyBaiduYuyin.__version__,
    packages=["PyBaiduYuyin"],
    include_package_data=True,

    # PyPI metadata
    author=PyBaiduYuyin.__author__,
    author_email="wang_changxu@icloud.com",
    description=PyBaiduYuyin.__doc__,
    long_description=open("README.rst").read(),
    license=PyBaiduYuyin.__license__,
    keywords="baidu voice service",
    url="https://github.com/DelightRun/PyBaiduYuyin#readme",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: BSD License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Other OS",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)