#
# test_http.py
#

import asyncio
from tests.utils import (
    setup_http_server,
    teardown_server
)


def test_create_server_and_connect():

    server, port = setup_http_server()
    print(port)

    @asyncio.coroutine
    def _client():
        # yield from asyncio.sleep(500)
        r, w = yield from asyncio.open_connection('127.0.0.1', port)
        assert isinstance(r, asyncio.StreamReader)
        w.write_eof()
        w.close()

    asyncio.get_event_loop().run_until_complete(_client())
    teardown_server(server)

    # asyncio.get_event_loop().close()


def test_server_bad_request():
    server, port = setup_http_server()

    @asyncio.coroutine
    def _client():
        r, w = yield from asyncio.open_connection('127.0.0.1', port)
        assert isinstance(r, asyncio.StreamReader)
        w.write(b"a98asdfyhsfhhb2l3irjwef\n")
        data = yield from asyncio.wait_for(r.read(1024), 1.0)
        assert data.startswith(b"HTTP/1.1 400 Bad Request")

    asyncio.get_event_loop().run_until_complete(_client())
    teardown_server(server)


if __name__ == "__main__":
    test_create_server_and_connect()
    test_server_bad_request()
