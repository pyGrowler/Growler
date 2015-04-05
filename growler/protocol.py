#
# growler/protocol.py
#
"""
Code containing Growler's asyncio.Protocol code for handling all streaming (TCP)
connections.
"""

import asyncio
import sys

class MetaGrowlerProtocol(asyncio.Protocol):
    pass

class GrowlerProtocol(asyncio.Protocol):
    """
    The protocol for handling all requests. The class hands off all data
    received to a responder object.
    """

    responder_type = None

    def __init__(self, responder_type=None):
        """
        Construct a GrowlerProtocol - this
        """
        if responder_type is not None:
            self.responder_type = responder_type

    def connection_made(self, transport):
        """
        asyncio.Protocol member - called upon when there is a new socket
        connection.
        @param transport asyncio.Transport: The Transport handling the socket
            communication
        """
        print("[connection made]")
        print(" ", transport.__class__)
        self.responders = [self.responder_type()]
        self.transport = transport
        self.hostname = transport.get_extra_info('peername')
        self.socket = transport.get_extra_info('socket')
        self.is_done_transmitting = False
        print("Growler Connection from {}".format(self.hostname))

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
        print("[server::data_received]", ">>", data)
        self.responders[-1].push_data(data)

    def eof_received(self):
        """
        asyncio.Protocol member - called upon when the client signals it will
        not be sending any more data to the server.
        """
        self.is_done_transmitting = True
        print("[eof_received]")


# Or should this be called HTTPGrowlerProtocol?
class GrowlerHTTPProtocol(GrowlerProtocol):
    """
    GrowlerProtocol dealing with HTTP requests
    """
    from .http.responder import HTTPResponder
    responder_type = HTTPResponder
