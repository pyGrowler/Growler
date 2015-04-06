#
# growler/__init__.py
#
#   Copyright (c) 2014 Andrew Kubera <andrew.kubera@gmail.com>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
"""
Growler is an http(s) server designed around the asyncio python module which
imitates Nodejs's express framework, allowing easy creation of complex websites
using a middleware-based configuration.
"""

import ssl
import asyncio
from importlib.machinery import SourceFileLoader
from os import path
from copy import copy
from pkg_resources import declare_namespace

import growler.app
import growler.router

from growler.http.server import create_server as create_http_server

metafile = path.join(path.dirname(__file__), "metadata.py")
metadata = SourceFileLoader("metadata", metafile).load_module()

__version__ = metadata.version
__author__ = metadata.author
__date__ = metadata.date
__copyright__ = metadata.copyright
__license__ = metadata.license

declare_namespace('growler')

App = growler.app.App
Router = growler.router.Router

DEFAULT_HTTP_OPTS = {'backlog': 100}


def create_https_server(options, callback=None, loop=None):
    """Creates an https 'server' object which may listen on multiple ports."""
    loop = loop or asyncio.get_event_loop()
    priv = options['key']
    pub = options['cert'] if 'cert' in options.keys() else None

    sslctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    if pub is None:
        sslctx.load_cert_chain(certfile=priv)
    else:
        sslctx.load_cert_chain(certfile=pub, keyfile=priv)

    return http_server(callback, loop, sslctx, "Creating HTTPS server")


def run_forever(loop=None):
    loop = loop or asyncio.get_event_loop()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("Keyboard induced termination : Exiting")
    finally:
        loop.close()


__all__ = [
    "App",
    "Router",
    "run_forever",
    "create_http_server",
    "create_https_server",
]
