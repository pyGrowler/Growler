#
# setup.py
#

import sys

from setuptools import setup, find_packages

install_requires = []
if sys.version_info < (3, 4):
  install_requires.append('asyncio==0.2.1')


setup(
  name="growler",
  version="0.1.0",
  author="Andrew Kubera",
  author_email="andrew.kubera@gmail.com",
  description = "A web framework covering the asyncio module (PEP 3156), intending to be similar to the nodejs 'Express' module.",
  classifiers=[
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.4",
  ],
  install_requires = install_requires,
  packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
)
