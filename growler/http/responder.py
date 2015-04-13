#
# growler/http/responder.py
#
"""
The Growler class responsible for responding to HTTP requests.
"""

import asyncio
from .parser import Parser


class GrowlerHTTPResponder():
    """
    The Growler Responder for HTTP connections. This class responds to incoming
    connections by parsing the incoming data as as ah HTTP request (using
    functions in growler.http.parser) and creating request and response objects
    which are finally passed to the app object found in protocol.
    """

    def __init__(self, protocol, parser_factory=Parser):
        """
        Construct an HTTPResponder.

        This should only be called from a growler protocol instance.

        @param protocol: The GrowlerHTTPProtocol which created the responder.
        """
        print("[HTTPResponder::HTTPResponder]")
        self._proto = protocol
        self.loop = protocol.loop
        self.parsing_queue = asyncio.Queue(loop=self.loop)
        self.parser = parser_factory(self.parsing_queue)
        self.endpoint = protocol.growler_app
        self.parsing_task = self.loop.create_task(self.on_parsing_queue())

    def on_data(self, data):
        """
        This is the function called by the http protocol upon receipt of
        incoming client data.
        """
        self.parser.consume(data)

    @asyncio.coroutine
    def on_parsing_queue(self):
        """
        The coroutine listening for some data on the queue
        """
        print("Beginning [on_parsing_queue]")
        self.parsed_request = yield from self.parsing_queue.get()
        print("first_line:", self.parsed_request)
        headers = yield from self.parsing_queue.get()
        print("headers:", headers)
