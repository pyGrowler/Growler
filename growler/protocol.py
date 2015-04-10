#
# growler/protocol.py
#
"""
Code containing Growler's asyncio.Protocol code for handling all streaming
(TCP) connections.
"""

import asyncio
import sys


class GrowlerProtocol(asyncio.Protocol):
    """
    The protocol for handling all requests. The class hands off all data
    received to a responder object.
    """

    responder_type = None

    def __init__(self, loop, responder_type):
        """
        Construct a GrowlerProtocol object.

        @param loop asyncio.BaseEventLoop: The event loop managing all
            asynchronous activity of this protocol
        @param responder_type: The type (not instance) of the responder to
            create upon creation of
        """
        print("[GrowlerProtocol::__init__]", id(self))
        self.responder_type = responder_type
        self.loop = asyncio.get_event_loop if loop is None else loop
        self.data_queue = asyncio.Queue()

    def connection_made(self, transport):
        """
        asyncio.Protocol member - called upon when there is a new socket
        connection. This creates a new responder (as determined by the member
        'responder_type') and stores in a list for

        @param transport asyncio.Transport: The Transport handling the socket
            communication
        """
        print("[GrowlerProtocol::connection_made]", id(self))

        self.responders = [self.responder_type(self)]
        self.transport = transport
        self.remote_hostname, self.remote_port = transport.get_extra_info(
                                                                    'peername')
        self.socket = transport.get_extra_info('socket')
        self.is_done_transmitting = False
        print("Growler Connection from {}:{}".format(self.remote_hostname,
                                                     self.remote_port))

    def connection_lost(self, exc):
        """
        asyncio.Protocol member - called upon when a socket closes.
        @param exc Exception: Error if unexpected closing. None if clean close
        """
        if exc:
            print("[connection_lost]", exc, file=sys.stderr)
        print("[connection_lost]")

    def data_received(self, data):
        """
        asyncio.Protocol member - called upon when there is data to be read
        @param transport bytes: bytes in the latest data transmission
        """
        self.loop.create_task(self.data_queue.put(data))
        # self.call_soon(self.self.responders[-1].)
        # print("[GrowlerProtocol::data_received]", id(self))
        # print("[server::data_received]", ">>", data)
        # print("Responders!",self.responders)
        # asyncio.async(self.responders[-1].data_queue.put,
        #               data,
        #               loop=self.loop)
        # self.responders[-1].on_data(data)

    def eof_received(self):
        """
        asyncio.Protocol member - called upon when the client signals it will
        not be sending any more data to the server.
        """
        self.loop.create_task(self.data_queue.put(None))
        self.is_done_transmitting = True
        print("[GrowlerProtocol::eof_received]")


# Or should this be called HTTPGrowlerProtocol?
class GrowlerHTTPProtocol(GrowlerProtocol):
    """
    GrowlerProtocol dealing with HTTP requests
    """
    from .http.responder import HTTPResponder

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
