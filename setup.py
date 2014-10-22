#
# setup.py
#

import sys

from setuptools import setup, find_packages

install_requires = ['termcolor', 'mako', 'pyjade']

if sys.version_info < (3, 4):
  install_requires.append('asyncio==0.2.1')

long_description = """
A web framework covering the asyncio module (PEP 3156), modeled loosely after
the NodeJS Connect/Express frameworks.
Growler uses a series of 'middleware' functions to manipulate the request and
response objects created for each connection. This stream/filter model makes it
very easy to modularize and extend web applications with any features, backed
by the power of python.

Currently Growler is single threaded, and not tested very well.

"""


setup(
  name= "growler",
  version= "0.1.0",
  author= "Andrew Kubera",
  license= "Apache v2.0",
  url= "https://github.com/pyGrowler/Growler",
  author_email= "andrew.kubera@gmail.com",
  description= "A micro web-framework using asyncio coroutines.",
  long_description= long_description,
  classifiers= [
    "Development Status :: 2 - Pre-Alpha",
    # "Framework :: Growler",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.4",
    "Topic :: Internet :: WWW/HTTP",
    "Natural Language :: English"
  ],
  install_requires = install_requires,
  packages= find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
  scripts= ['scripts/growler-init']
)
