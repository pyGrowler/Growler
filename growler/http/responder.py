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

    def __init__(self, protocol):
        """
        Construct an HTTPResponder.

        This should only be called from a growler protocol instance.

        @param protocol: The GrowlerHTTPProtocol which created the responder.
        """
        print("[HTTPResponder::HTTPResponder]")
        self._proto = protocol
        self.loop = protocol.loop
        self.parsing_queue = asyncio.Queue(loop=self.loop)
        self.parser = Parser(self.parsing_queue)
        self.endpoint = protocol.growler_app
        # self.send_data_task = self._proto.loop.create_task(self.parser.send(data))

    def __del__(self):
        self.parsing_queue.close()

    def on_data(self, data):
        """
        The responder's on_data function gets passed a value
        """
        self.parser.consume(data)

    @asyncio.coroutine
    def data_loop(self):
        count = 0
        while True:
            data = yield from self.data_queue.get()
            self.on_data(data)
            if data is None:
                break
            count += 1

    @asyncio.coroutine
    def on_parsing_queue(self):
        print("Beginning [on_parsing_queue]")
        first_line = yield from self.parsing_queue.get()
        print("first_line:", first_line)
        headers = yield from self.parsing_queue.get()
        print("headers:", headers)
