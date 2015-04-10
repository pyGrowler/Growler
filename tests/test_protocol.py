#
# tests/test_protocol.py
#

import pytest
import growler.protocol
from utils import *

import asyncio

class TestResponder:

    def __init__(self, something):
        print("something")

class TestProtocol(growler.protocol.GrowlerProtocol):
    responder_type = TestResponder

def test_constructor():
    loop = asyncio.get_event_loop()
    proto = growler.protocol.GrowlerProtocol(loop, TestResponder)
    assert isinstance(proto, asyncio.Protocol)

def setup_server(loop=asyncio.get_event_loop(), port=8888):
    """
    Sets up a GrowlerProtocol server for testing
    """
    # proto = growler.protocol.GrowlerProtocol
    proto = TestProtocol
    coro = loop.create_server(proto, '127.0.0.1', port)
    server = loop.run_until_complete(coro)
    return server

def teardown_server(server, loop=asyncio.get_event_loop()):
    server.close()
    loop.run_until_complete(server.wait_closed())

def test_responder():
    class mock_transport:
        def get_extra_info(self, key):
            return {
                'peername': ('mock.host', -1)
            }.get(key, None)

        def write(self, data):
            print("writing ",len(data),"bytes")
        def close(self):
            pass
    loop = asyncio.get_event_loop()
    trans = mock_transport()
    proto = growler.protocol.GrowlerProtocol(loop, TestResponder)
    proto.responder_type = TestResponder
    proto.connection_made(trans)
    trans.write(b"x")
    trans.close()

def test_create_server():

    port = random_port()

    server = setup_server(port=port)

    @asyncio.coroutine
    def _client():
        # with pytest.raises(Exception):
        r,w = yield from asyncio.open_connection('127.0.0.1', port)
        assert r is not None
        assert w is not None

        w.write_eof()
        w.close()

    asyncio.get_event_loop().run_until_complete(_client())
    teardown_server(server)
    # asyncio.get_event_loop().close()

def test_server_timeout():
    port = random_port()
    server = setup_server(port=port)
    loop = asyncio.get_event_loop()

    @asyncio.coroutine
    def _client():
        r,w = yield from asyncio.open_connection('127.0.0.1', port)
        assert r is not None

    loop.run_until_complete(_client())
    teardown_server(server)
    loop.close()

if __name__ == '__main__':
    test_constructor()
    test_create_server()
    test_responder()
    test_missing_responder()
    test_server_timeout()
