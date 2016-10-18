#
# growler/__init__.py
#
# flake8: noqa
#
#   Copyright (c) 2016 Andrew Kubera <andrew.kubera@gmail.com>
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
A general purpose asynchronous framework, supporting the asynchronous
primitives (async/await) introduced in Python 3.5.

The original goal was to serve http, and while this capability is still
built-in (see growler.http), the structure of Growler allows for a
larger set of capabilities.

To get started, import `Growler` from this package and create an
instance (customarily named 'app'). Add functionality to the app object
via the 'use' method decorator over your functions. This functions
may be asynchronous, and must accept a request and response object.
These are called (in the same order as 'use'd) upon a client connection.

Growler does not include its own server or event loop - but provides a
standard asynchronous interface to be used with an event loop of the users
choosing. Python includes its own event-loop package, asyncio, which
works fine with Growler. The asyncio interface is located in
`growler.aio`; this is merely a convience for quick startup, asyncio is
not required (or even imported) unless the user wants to.
"""

from .__meta__ import (
    version as __version__,
    author as __author__,
    date as __date__,
    copyright as __copyright__,
    license as __license__,
)

from .core.application import (
    Application,
    GrowlerStopIteration,
)
from .core.router import (
    Router,
    RouterMeta,
    routerclass,
    get_routing_attributes
)
from .core.middleware_chain import (
    MiddlewareChain,
)

# alias Application
Growler = App = Application

__all__ = [
    "App",
    "Growler",
    "Application",
    "Router",
]
