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
Growler is an http(s) server and micro-framework designed around the asyncio
python module, introduced in python3.4. The goal of this project is to imitate
the successful Nodejs express framework, which allowing easy creation
of complex websites using a middleware-based configuration.
"""

from importlib.machinery import SourceFileLoader
from os import path
from pkg_resources import declare_namespace

metafile = path.join(path.dirname(__file__), "metadata.py")
metadata = SourceFileLoader("metadata", metafile).load_module()

__version__ = metadata.version
__author__ = metadata.author
__date__ = metadata.date
__copyright__ = metadata.copyright
__license__ = metadata.license

declare_namespace('growler')

import growler.application
import growler.router

from growler.http.server import create_server as create_http_server


App = growler.application.Application
Router = growler.router.Router

__all__ = [
    "App",
    "Router",
    "run_forever",
    "create_http_server",
    "create_https_server",
]
