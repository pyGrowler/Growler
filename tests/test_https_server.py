#
# tests/test_https_server.py
#

import os
import ssl
import pytest
import asyncio

import growler

SSL_KEYFILE = 'PYTEST.key'
SSL_CERFILE = 'PYTEST.crt'


@pytest.fixture # (scope='session')
def ssl_ctx(event_loop, tmpdir):
    os.chdir(str(tmpdir))
    os.system("openssl req -batch -newkey rsa:2048 -nodes "
              "-keyout {key} -x509 -days 1 -out {crt}".format(key=SSL_KEYFILE, crt=SSL_CERFILE))
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(SSL_CERFILE, SSL_KEYFILE)
    return ssl_context


@pytest.fixture
def hostname():
    return '127.0.0.1'


@pytest.fixture
def app(event_loop):
    app = growler.App(loop=event_loop)
    return app


@pytest.fixture
def growler_server(app, event_loop, hostname, unused_tcp_port, ssl_ctx):
    return app.create_server(host=hostname,
                             port=unused_tcp_port,
                             ssl=ssl_ctx,
                             as_coroutine=True)

@pytest.fixture
def make_client(hostname, unused_tcp_port, event_loop):
    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context.check_hostname = False
    ssl_context.load_verify_locations(SSL_CERFILE)
    return asyncio.open_connection(host=hostname,
                                   port=unused_tcp_port,
                                   ssl=ssl_context)

@pytest.fixture
def did_send():
    return []


@pytest.fixture
def loaded_app(app, did_send):
    @app.get("/")
    def index(req, res):
        res.send_text("Foobar!")
        did_send.append(True)
        # assert req.peercert is None
    return app


@pytest.mark.asyncio
async def test_foo(loaded_app, growler_server, make_client, did_send):
    assert len(did_send) == 0

    # make the server/client
    server = await growler_server
    reader, writer = await make_client

    # send request to the server
    writer.write(b'\r\n'.join([
        b"GET / HTTP/1.1", b'host: localhost', b'\r\n',
    ]))
    await writer.drain()
    # writer.write_eof()

    # async def timeout(t, coro):
    #     sleeper = asyncio.sleep(t)
    #     await asyncio.wait([sleeper, coro])

    # wait for a response
    response = await asyncio.wait_for(reader.read(), 1)

    assert did_send[0] is True

    try:
        assert response.startswith(b'HTTP/1.1 200 OK')
        assert response.endswith(b'Foobar!')
    finally:
        writer.close()
        server.close()
    # print("client", client)
    # assert None
