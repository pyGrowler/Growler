#
# growler/http/protocol.py
#
"""
Code containing Growler's asyncio.Protocol code for handling HTTP requests.
"""

import asyncio
import sys


class HttpProtocol(asyncio.Protocol):
    """
    The protocol for handling HTTP requests as implemented by the Growler
    project.
    """

    def connection_made(self, transport):
        """
        asyncio.Protocol member - called upon when there is a new socket
        connection.
        @param transport asyncio.Transport: The Transport handling the socket
            communication
        """
        self.transport = transport
        self.hostname = transport.get_extra_info('peername')
        self.socket = transport.get_extra_info('socket')
        self.is_done_transmitting = False
        print("HTTP Connection from {}".format(self.hostname))

    def connection_lost(self, exc):
        """
        asyncio.Protocol member - called upon when a socket closes.
        @param exc Exception: Error if unexpected closing. None if clean close
        """
        if exc:
            print("[connection_lost]", exc, file=sys.stderr)

    def data_received(self, data):
        """
        asyncio.Protocol member - called upon when there is data to be read
        @param transport bytes: bytes in the latest data transmission
        """
        from base64 import b64encode
        print('[data_received] ', b64encode(data))

        # close the socket?
        self.transport.close()

    def eof_received(self):
        """
        asyncio.Protocol member - called upon when the client signals it will
        not be sending any more data to the server.
        """
        self.is_done_transmitting = True
