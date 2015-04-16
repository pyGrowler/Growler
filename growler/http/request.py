#
# growler/http/request.py
#

from urllib.parse import (unquote, urlparse, parse_qs)
from .Error import (
    HTTPErrorBadRequest,
    HTTPErrorVersionNotSupported,
    HTTPErrorNotImplemented
)

from . import Parser
from termcolor import colored

import asyncio


class HTTPRequest(object):
    """
    Helper class which handles the parsing of an incoming http request.
    The usage should only be from an HTTPRequest object calling the parse()
    function.
    """

    def __init__(self, protocol, headers):
        """
        The HTTPRequest object is all the information you could want about the
        incoming http connection. It gets passed along with the HTTPResponse
        object to all the middleware of the app.

        @param protocol growler.HTTPProtocol: A reference to the protocol which
            was responsible for handling the client's request and creating this
            HTTPRequest object.

        @param headers dict: The headers gathered from the incoming stream
        """
        self._protocol = protocol
        self.ip = protocol.socket.getpeername()[0]
        self.protocol = 'https' if protocol.cipher else 'http'
        self.app = protocol.http_application
        self.headers = headers
        self.hostname = headers['HOST']
        self.originalURL = protocol.request['url']
        self.body = asyncio.Future() if 'CONTENT-LENGTH' in headers else None
        self.path = ''

    def param(self, name, default=None):
        """
        Return value of HTTP parameter 'name' if found, else return provided
        'default'

        @param name: Key to search the query dict for
        @type name: str

        @param default: Returned if 'name' is not found in the query dict
        """
        try:
            return self.query[name]
        except KeyError:
            return default

    def get_body(self, timeout=0):
        """
        A helper function which blocks until the body has been read completely.
        Returns the bytes of the body which the user should decode. An optional
        timeout parameter can be set to throw an asyncio.TimeoutError if the
        body does not complete before 'timeout' number of seconds.

        If the request does not have a body part (i.e. it is a GET request)
        this function returns None
        """
        if self.body is None:
            return None
        coro = asyncio.wait_for(self.body, timeout, loop=self._protocol.loop)
        self._protocol.loop.run_until_complete(coro)
        return self.body.result()
