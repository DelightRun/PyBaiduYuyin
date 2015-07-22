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
    author_email="Changxu.mail@gmail.com",
    description=PyBaiduYuyin.__doc__,
    long_description=open("README.rst").read(),
    license=PyBaiduYuyin.__license__,
    keywords="baidu voice service",
    url="https://github.com/DelightRun/PyBaiduYuyin",
)
