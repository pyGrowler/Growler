#
# tests/test_protocol.py
#

import pytest
import growler.protocol

import asyncio


class TestResponder:

    def __init__(self, something):
        print("something")

    def on_data(self, data):
        pass


class TestProtocol(growler.protocol.GrowlerProtocol):
    responder_type = TestResponder


def test_constructor():
    loop = asyncio.get_event_loop()
    proto = growler.protocol.GrowlerProtocol(loop, TestResponder)
    assert isinstance(proto, asyncio.Protocol)


def setup_server(port, loop=asyncio.get_event_loop()):
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
            print("writing", len(data), "bytes")

        def close(self):
            pass
    loop = asyncio.get_event_loop()
    trans = mock_transport()
    proto = growler.protocol.GrowlerProtocol(loop, TestResponder)
    proto.responder_type = TestResponder
    proto.connection_made(trans)
    trans.write(b"x")
    trans.close()


def test_create_server(unused_tcp_port):

    port = unused_tcp_port
    server = setup_server(port=port)

    @asyncio.coroutine
    def _client():
        # with pytest.raises(Exception):
        r, w = yield from asyncio.open_connection('127.0.0.1', port)
        assert r is not None
        assert w is not None

        w.write_eof()
        w.close()

    asyncio.get_event_loop().run_until_complete(_client())
    teardown_server(server)


def test_server_timeout(unused_tcp_port, event_loop=asyncio.get_event_loop()):
    server = setup_server(port=unused_tcp_port, loop=event_loop)

    @asyncio.coroutine
    def _client():
        r, w = yield from asyncio.open_connection('127.0.0.1', unused_tcp_port)
        assert r is not None

    event_loop.run_until_complete(_client())
    teardown_server(server)


def test_missing_responder():
    with pytest.raises(TypeError):
        proto = growler.protocol.GrowlerProtocol(asyncio.get_event_loop(),
                                                 lambda arg: None)
        proto.connection_made(None)

if __name__ == '__main__':
    test_constructor()
    test_create_server()
    test_responder()
    test_missing_responder()
    test_server_timeout()
