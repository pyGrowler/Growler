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

PACKAGES = find_packages(
    exclude=["*.tests", "*.tests.*", "tests.*", "tests"]
)

NAMESPACES = [
    'growler',
    'growler.ext',
    'growler.middleware',
    'growler.mw',
]

setup(
    name="growler",
    version=metadata.version,
    author=metadata.author,
    license=metadata.license,
    url=metadata.url,
    author_email=metadata.author_email,
    description=__doc__,
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
    packages=PACKAGES,
    namespace_packages=NAMESPACES,
    platforms='all',
    scripts=glob('scripts/*')
)
