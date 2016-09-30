#
# tests/test_server.py
#

import pytest
import asyncio
import growler


@pytest.fixture
def app(event_loop):
    app = growler.App(loop=event_loop)
    return app


@pytest.fixture
def growler_server(app, event_loop, unused_tcp_port):
    return app.create_server(host='127.0.0.1',
                                          port=unused_tcp_port,
                                          gen_coroutine=True,
                                          ) # loop=event_loop)


@pytest.mark.asyncio
def test_post_request(app, growler_server, event_loop, unused_tcp_port):
    body_data = None
    response_data = None

    did_send = False
    did_receive = False

    server = yield from growler_server

    @app.post('/data')
    @asyncio.coroutine
    def post_test(req, res):
        nonlocal body_data, did_receive
        body_data = yield from req.body
        did_receive = True
        res.send_text("OK")


    @asyncio.coroutine
    def http_request():
        nonlocal did_send, response_data
        did_send = True
        r, w = yield from asyncio.open_connection(host='127.0.0.1',
                                                    port=unused_tcp_port,
                                                    loop=event_loop)

        data = b'{"somekey": "somevalue"}'

        request_headers = '\r\n'.join([
            'POST /data HTTP/1.1',
            'HOST: localhost',
            'Content-Type: application/json',
            'ConTent-LENGTH: %d' % len(data),
            '\r\n',
        ]).encode()

        w.write(request_headers)
        w.write(data)
        w.write_eof()

        response_data = yield from r.read()
        server.close()

    yield from http_request()
    server.close()

    assert did_send
    assert did_receive
    assert body_data == b'{"somekey": "somevalue"}'
    assert response_data.endswith(b'\r\n\r\nOK')
