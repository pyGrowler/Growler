#
# growler/http/protocol.py
#
"""
Code containing Growler's asyncio.Protocol code for handling HTTP requests.
"""

from growler.protocol import GrowlerProtocol
from growler.http.responder import HTTPResponder

import asyncio
import sys

# Or should this be called HTTPGrowlerProtocol?
class GrowlerHTTPProtocol(GrowlerProtocol):
    """
    GrowlerProtocol dealing with HTTP requests
    """

    def __init__(self, app, loop):
        """
        Construct a GrowlerHTTPProtocol object. This should only be called from
        a growler.HTTPServer instance.

        @param app: A growler application which
        @param loop:
        """
        super().__init__(loop=loop, responder_type=HTTPResponder)
        print("[GrowlerHTTPProtocol::__init__]", id(self))
        self.growler_app = app
