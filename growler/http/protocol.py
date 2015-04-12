#
# growler/http/protocol.py
#
"""
Code containing Growler's asyncio.Protocol code for handling HTTP requests.
"""

from growler.protocol import GrowlerProtocol
from growler.http.responder import GrowlerHTTPResponder

import asyncio
import sys

# Or should this be called HTTPGrowlerProtocol?
class GrowlerHTTPProtocol(GrowlerProtocol):
    """
    GrowlerProtocol dealing with HTTP requests. Objects are created with a
    growler.App instance, which contains the relevant event_loop. The default
    responder_type is GrowlerHTTPResponder, which does the data parsing and
    req/res creation.
    """

    def __init__(self, app):
        """
        Construct a GrowlerHTTPProtocol object. This should only be called from
        a growler.HTTPServer instance (or any asyncio.create_server function).

        @param app: Typically a growler application which is the 'endpoint' for this
            protocol, but any callable with a 'loop' attribute should work.
        """
        super().__init__(loop=app.loop, responder_type=GrowlerHTTPResponder)
        print("[GrowlerHTTPProtocol::__init__]", id(self))
        self.growler_app = app
