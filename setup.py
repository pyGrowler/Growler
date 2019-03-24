#!/usr/bin/env python3
#
# setup.py
#

from importlib.machinery import SourceFileLoader
from setuptools import setup

metadata = SourceFileLoader("metadata", "growler/__meta__.py").load_module()

tar_url = 'https://github.com/pyGrowler/growler/archive/v%s.tar.gz' % (metadata.version)  # noqa

setup(
    version=metadata.version,
    license=metadata.license,
    url=metadata.url,
    download_url=tar_url,
)
