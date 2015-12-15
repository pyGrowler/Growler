#
# growler/__init__.py
#
# flake8: noqa
#
#   Copyright (c) 2015 Andrew Kubera <andrew.kubera@gmail.com>
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

# This ensures 'types' has the coroutine decorator, added in python3.5
# with same functionality as asyncio.coroutine in python3.4
import types
if not hasattr(types, 'coroutine'):
    import asyncio
    types.coroutine = asyncio.coroutine

from .__meta__ import (
    version as __version__,
    author as __author__,
    date as __date__,
    copyright as __copyright__,
    license as __license__,
)

import growler.application
import growler.router
import growler.protocol
import growler.middleware_chain
import growler.middleware

App = growler.application.Application
Router = growler.router.Router
GrowlerProtocol = growler.protocol.GrowlerProtocol
MiddlewareChain = growler.middleware_chain.MiddlewareChain

__all__ = [
    "App",
    "Router",
    "GrowlerProtocol",
]

# remove growler as a child
del growler
