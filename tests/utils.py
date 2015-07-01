#
# tests/utils
#
"""
Useful functions for all tests
"""

import asyncio
from growler.http.protocol import GrowlerHTTPProtocol
import growler


def random_port():
    from random import randint
    return randint(1024, 2**16)


def setup_test_server(unused_tcp_port, loop=asyncio.get_event_loop()):
    """
    Sets up a GrowlerProtocol server for testing
    """
    # proto = growler.protocol.GrowlerProtocol
    proto = TestProtocol
    coro = loop.create_server(proto, '127.0.0.1', unused_tcp_port)
    server = loop.run_until_complete(coro)
    return server


def setup_http_server(loop=asyncio.get_event_loop(), port=random_port()):
    """
    Sets up a GrowlerHTTPProtocol server for testing
    """
    # proto = growler.protocol.GrowlerHTTPProtocol
    app = growler.App()

    def proto():
        return GrowlerHTTPProtocol(app)
    coro = loop.create_server(proto, '127.0.0.1', port)
    server = loop.run_until_complete(coro)
    return server, port


def teardown_server(server, loop=asyncio.get_event_loop()):
    """
    'Generic' tear down a server and wait on the loop for everything to close.
    """
    server.close()
    loop.run_until_complete(server.wait_closed())
