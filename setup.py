#
# setup.py
#

from os import path
from glob import glob
from importlib.machinery import SourceFileLoader
from setuptools import setup, find_packages

metafile = path.join(".", "growler", "metadata.py")
metadata = SourceFileLoader("metadata", metafile).load_module()

REQUIRES = [
    'termcolor',
    'mako'
]

OPTIONAL_REQUIRES = {
  'jade': ['pyjade'],
  ':python_version=="3.3"': ['asyncio>=0.2.1']
}

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
    name="growler",
    version=metadata.version,
    author=metadata.author,
    license=metadata.license,
    url="https://github.com/pyGrowler/Growler",
    author_email=metadata.author_email,
    description="A micro web-framework using asyncio coroutines.",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Web Environment",
        "Operating System :: OS Independent",
        # "Framework :: Growler",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Topic :: Internet :: WWW/HTTP",
        "Natural Language :: English"
    ],
    install_requires=REQUIRES,
    extras_require=OPTIONAL_REQUIRES,
    packages=find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]
    ),
    platforms='all',
    scripts=glob('scripts/*')
)
