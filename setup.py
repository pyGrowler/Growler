#!/usr/bin/env python3
#
# setup.py
#

from setuptools import setup


metadata = {}
with open("growler/__meta__.py") as f:
    exec(f.read(), metadata)

tar_url = 'https://github.com/pyGrowler/growler/archive/v%s.tar.gz' % (metadata['version'])  # noqa

# Other metadata and options can be found in setup.cfg
setup(
    version=metadata['version'],
    license=metadata['license'],
    url=metadata['url'],
    download_url=tar_url,
)
