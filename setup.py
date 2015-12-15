#
# setup.py
#
"""
A micro web-framework using asyncio coroutines and chained middleware.
"""

from os import path
from glob import glob
from imp import load_source
from setuptools import setup, find_packages

metadata = load_source("metadata", path.join("growler", "__meta__.py"))

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

PACKAGES = find_packages(
    exclude=["*.tests", "*.tests.*", "tests.*", "tests"]
)

NAMESPACES = [
    'growler_ext',
]

CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Environment :: Web Environment",
    "Operating System :: OS Independent",
    # "Framework :: Growler",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.5",
    "Topic :: Internet :: WWW/HTTP",
    "Natural Language :: English"
]

tar_url = 'https://github.com/pygrowler/growler/archive/v%s.tar.gz' % (metadata.version)  # noqa

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
    namespace_packages=NAMESPACES,
    platforms='all',
    scripts=glob('scripts/*')
)
