#
# tests/utils
#
"""
Useful functions for all tests
"""

import asyncio
import pytest
from growler.http.protocol import GrowlerHTTPProtocol
import growler


def random_port():
    from random import randint
    return randint(1024, 2**16)

@asyncio.coroutine
def setup_test_server(unused_tcp_port, event_loop):
    """
    Sets up a GrowlerProtocol server for testing
    """
    # proto = growler.protocol.GrowlerProtocol
    proto = TestProtocol
    server = yield from event_loop.create_server(proto, '127.0.0.1', unused_tcp_port)
    return server, unused_tcp_port


@asyncio.coroutine
def setup_http_server(loop, port):
    """
    Sets up a GrowlerHTTPProtocol server for testing
    """
    # proto = growler.protocol.GrowlerHTTPProtocol
    app = growler.App()

    def proto():
        return GrowlerHTTPProtocol(app)

    return (yield from loop.create_server(proto, '127.0.0.1', port))


def teardown_server(server, loop=asyncio.get_event_loop()):
    """
    'Generic' tear down a server and wait on the loop for everything to close.
    """
    server.close()
    loop.run_until_complete(server.wait_closed())
