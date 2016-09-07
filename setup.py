#!/usr/bin/env python3
#
# setup.py
#
"""
A micro web-framework using asyncio coroutines and chained middleware.
"""

from glob import glob
from importlib.machinery import SourceFileLoader
from setuptools import setup, find_packages

metadata = SourceFileLoader("metadata", "growler/__meta__.py").load_module()

REQUIRES = [
]

OPTIONAL_REQUIRES = {
    'jade': ['pyjade'],
    'mako': ['growler-mako'],
    ':python_version=="3.3"': ['asyncio>=3.4.3'],
}

TESTS_REQUIRE = [
    'pytest',
    'pytest-asyncio',
]

SETUP_REQUIRES = [
    'pytest-runner',
]

PACKAGES = find_packages(
    exclude=["*.tests", "*.tests.*", "tests.*", "tests"]
)

CLASSIFIERS = [
    "Development Status :: 3 - Alpha",
    "Environment :: Web Environment",
    "Operating System :: OS Independent",
    # "Framework :: Growler",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Topic :: Internet :: WWW/HTTP",
    "Natural Language :: English"
]

tar_url = 'https://github.com/pyGrowler/growler/archive/v%s.tar.gz' % (metadata.version)  # noqa

setup(
    name="growler",
    version=metadata.version,
    author=metadata.author,
    license=metadata.license,
    url=metadata.url,
    download_url=tar_url,
    author_email=metadata.author_email,
    description=__doc__.strip(),
    classifiers=CLASSIFIERS,
    install_requires=REQUIRES,
    extras_require=OPTIONAL_REQUIRES,
    tests_require=TESTS_REQUIRE,
    packages=PACKAGES,
    setup_requires=SETUP_REQUIRES,
    platforms='all',
    scripts=glob('scripts/*')
)
