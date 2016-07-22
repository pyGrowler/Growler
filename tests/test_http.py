#
# test_http.py
#

import asyncio
import pytest
from utils import (
    setup_http_server,
    teardown_server
)


@pytest.mark.asyncio
def test_create_server_and_connect(event_loop, unused_tcp_port):

    server = yield from setup_http_server(event_loop, unused_tcp_port)
    # host, port = server.sockets[0].getpeername()
    # print(type(server.sockets[0]), dir(server.sockets[0]))
    print(unused_tcp_port)

    @asyncio.coroutine
    def _client():
        # yield from asyncio.sleep(500)
        r, w = yield from asyncio.open_connection('127.0.0.1', unused_tcp_port)
        assert isinstance(r, asyncio.StreamReader)
        w.write_eof()
        w.close()

    yield from _client()
    # teardown_server(server)


@pytest.mark.asyncio
def test_server_bad_request(event_loop, unused_tcp_port):
    server = yield from setup_http_server(event_loop, unused_tcp_port)

    @asyncio.coroutine
    def _client():
        r, w = yield from asyncio.open_connection('127.0.0.1', unused_tcp_port)
        assert isinstance(r, asyncio.StreamReader)
        w.write(b"a98asdfyhsfhhb2l3irjwef\n")
        data = yield from asyncio.wait_for(r.read(1024), 1.0)
        assert data.startswith(b"HTTP/1.1 400 Bad Request")

    yield from _client()
    # teardown_server(server)


if __name__ == "__main__":
    test_create_server_and_connect()
    test_server_bad_request()
