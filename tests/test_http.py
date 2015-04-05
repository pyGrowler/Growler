#
# test_http.py
#

import growler.protocol
import asyncio
from utils import *

def setup_server(loop=asyncio.get_event_loop(), port=8888):
    """
    Sets up a GrowlerProtocol server for testing
    """
    proto = growler.protocol.GrowlerHTTPProtocol
    coro = loop.create_server(proto, '127.0.0.1', port)
    server = loop.run_until_complete(coro)
    return server


def teardown_server(server, loop=asyncio.get_event_loop()):
    server.close()
    loop.run_until_complete(server.wait_closed())

def test_create_server_and_connect():

    port = random_port()
    server = setup_server(port=port)

    @asyncio.coroutine
    def _client():
        r,w = yield from asyncio.open_connection('127.0.0.1', port)
        assert isinstance(r, asyncio.StreamReader)
        w.write_eof()
        w.close()

    asyncio.get_event_loop().run_until_complete(_client())
    teardown_server(server)
    # asyncio.get_event_loop().close()

def test_server_bad_request():

    port = random_port()
    server = setup_server(port=port)

    @asyncio.coroutine
    def _client():
        r,w = yield from asyncio.open_connection('127.0.0.1', port)
        assert isinstance(r, asyncio.StreamReader)
        w.write(b"a98asdfyhsfhhb2l3irjwef")
        data = yield from r.read(1024)
        print
        w.write_eof()
        w.close()


    asyncio.get_event_loop().run_until_complete(_client())
    teardown_server(server)
