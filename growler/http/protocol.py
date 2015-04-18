#
# growler/http/protocol.py
#
"""
Code containing Growler's asyncio.Protocol code for handling HTTP requests.
"""

from growler.protocol import GrowlerProtocol
from growler.http.responder import GrowlerHTTPResponder
from growler.http.errors import (
    HTTPErrorInternalServerError
)

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

        @param app: Typically a growler application which is the 'endpoint' for
            this protocol, but any callable with a 'loop' attribute should
            work.
        """
        super().__init__(loop=app.loop, responder_factory=GrowlerHTTPResponder)
        print("[GrowlerHTTPProtocol::__init__]", id(self))
        self.http_application = app
        self.make_responder = lambda _self: GrowlerHTTPResponder(
                                _self,
                                request_factory=app._request_class,
                                response_factory=app._response_class
                                )

    def middleware_chain(self, req, res):
        """
        Runs through the chain of middleware in app.
        """
        for mw in self.http_application.middleware_chain(req):
            try:
                if asyncio.iscoroutine(mw):
                    print("Running middleware coroutine:", mw)
                    asyncio.run_until_complete(mw(req, res), loop=self.loop)
                else:
                    print("Running middleware:", mw)
                    mw(req, res)
            except Exception as error:
                for handler in self.http_application.next_error_handler(req):
                    handler(req, res, error)
                break

        if not res.has_ended:
            raise HTTPErrorInternalServerError
