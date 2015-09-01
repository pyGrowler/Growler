#
# setup.py
#
"""
A micro web-framework using asyncio coroutines and chained middleware.
"""

from os import path
from glob import glob
from importlib.machinery import SourceFileLoader
from setuptools import setup, find_packages

metafile = path.join(".", "growler", "__meta__.py")
metadata = SourceFileLoader("metadata", metafile).load_module()

REQUIRES = [
    'mako'
]

OPTIONAL_REQUIRES = {
    'jade': ['pyjade'],
    ':python_version=="3.3"': ['asyncio>=0.2.1']
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
    classifiers=[
        "Development Status :: 4 - Beta",
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
    tests_require=TESTS_REQUIRE,
    packages=PACKAGES,
    namespace_packages=NAMESPACES,
    platforms='all',
    scripts=glob('scripts/*')
)
