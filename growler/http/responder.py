#
# growler/http/responder.py
#
"""
The Growler class responsible for responding to HTTP requests.
"""

import asyncio

from .parser import Parser
from .request import HTTPRequest
from .response import HTTPResponse


class GrowlerHTTPResponder():
    """
    The Growler Responder for HTTP connections. This class responds to incoming
    connections by parsing the incoming data as as ah HTTP request (using
    functions in growler.http.parser) and creating request and response objects
    which are finally passed to the app object found in protocol.
    """

    def __init__(self,
                 protocol,
                 parser_factory=Parser,
                 request_factory=HTTPRequest,
                 response_factory=HTTPResponse
                 ):
        """
        Construct an HTTPResponder.

        This should only be called from a growler protocol instance.

        @param protocol: The GrowlerHTTPProtocol which created the responder.
        """
        self._proto = protocol
        self.loop = protocol.loop
        self.parser = parser_factory(self)
        self.endpoint = protocol.growler_app
        self.on_data = self.parser.consume
        self.build_req = request_factory
        self.build_res = response_factory

    def on_data(self, data):
        """
        This is the function called by the http protocol upon receipt of
        incoming client data.
        """
        self.parser.consume(data)

    def set_request_line(self, method, url, version):
        """
        Sets the request line on the responder.
        """
        self.parsed_request = (method, url, version)

    def set_headers(self, headers):
        """
        Sets the headers attribute and triggers the beginning of the req/res
        construction.
        """
        print("Beginning [on_parsing_queue]")
        self.headers = headers

    def build_req_res(self):
        req = self.build_req(self._proto, self.headers)
        res = self.build_res(None)
        return req, res
