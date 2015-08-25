#
# tests/test_http_responder.py
#

import growler
from growler.http.responder import GrowlerHTTPResponder
from growler.http.methods import HTTPMethod

import asyncio
import pytest
from unittest import mock

from mocks import *

from test_http_protocol import (
    mock_app,
    mock_req_factory,
    mock_res_factory,
    mock_req,
    mock_res,
    mock_parser,
    mock_parser_factory,
)

from mock_classes import (
    responder,
    request_uri,
)

GET = HTTPMethod.GET
POST = HTTPMethod.POST
PUT = HTTPMethod.PUT
DELETE = HTTPMethod.DELETE

@pytest.fixture
def app(mock_event_loop):
    app = mock.Mock(spec=growler.application.Application)
    app.loop = mock_event_loop
    return app


@pytest.fixture
def mock_protocol(app):
    protocol = mock.Mock(spec=growler.http.protocol.GrowlerHTTPProtocol)
    protocol.http_application = app
    protocol.loop = app.loop
    protocol.client_headers = None
    return protocol


@pytest.fixture
def responder(mock_protocol,
              mock_parser_factory,
              mock_req_factory,
              mock_res_factory):
    resp = GrowlerHTTPResponder(mock_protocol,
                                parser_factory=mock_parser_factory,
                                request_factory=mock_req_factory,
                                response_factory=mock_res_factory
                                )
    return resp

def test_responder_constructor(mock_protocol):
    r = GrowlerHTTPResponder(mock_protocol)
    assert r.loop is mock_protocol.loop
    assert r.headers is None


@pytest.mark.parametrize("data", [
    b'',
    b'GET /',
    b'GET / HTTP/1.1\n',
    b'GET / HTTP/1.1\n\nblahh',
])
def test_on_data_no_headers(responder, mock_parser, data):
    mock_parser.consume.return_value = None
    responder.on_data(data)
    assert responder.headers is None
    mock_parser.consume.assert_called_with(data)


@pytest.mark.parametrize("data", [
    b'1234567',
    # b'GET /',
    # b'GET / HTTP/1.1\n',
    # b'GET / HTTP/1.1\n\nblahh',
])
def test_on_data_post_headers(responder,
                              mock_parser,
                              mock_req,
                              mock_res,
                              app,
                              data,
                              ):
    mock_req.body = mock.Mock(spec=asyncio.Future)

    def on_consume(d):
        responder.headers = mock.MagicMock()
        responder.headers.__getitem__.return_value = len(data)
        responder.content_length = 0
        responder.body_buffer = []
        return data

    mock_parser.consume.side_effect = on_consume

    responder.on_data(data)

    assert responder.req is mock_req
    assert responder.res is mock_res
    assert responder.loop.create_task.called
    responder.app.handle_client_request.assert_called_with(mock_req, mock_res)


@pytest.mark.parametrize("data, length", [
    (b' ' * 10, 100),
    (b'_' * 99, 10),
])
def notest_bad_content_length(responder, mock_parser, data, length):
    mock_parser.client_headers = {'CONTENT-LENGTH': length}
    h = responder.headers
    responder.content_length = 500

    with pytest.raises(growler.http.errors.HTTPErrorBadRequest) as e:
        responder.validate_and_store_body_data(data)

    assert e.value.phrase == "Unexpected body data sent"


@pytest.mark.parametrize("method, request_uri, clength", [
    (GET, '/', None),
    (POST, '/', 0),
    (PUT, '/', 0),
    (DELETE, '/', None)
])
def test_set_request_line_content_length(responder, method, request_uri, clength):
    responder.set_request_line(method, request_uri, "HTTP/1.1")
    assert responder.content_length is clength


def notest_on_parsing_queue(mock_protocol):
    loop = asyncio.get_event_loop()
    r = GrowlerHTTPResponder(mock_protocol, mock_parser)
    r.parsing_task.cancel()

    @asyncio.coroutine
    def _():
        output = yield from r.parsing_queue.get()
        assert output == 'spam'

    r.parsing_queue.put_nowait('spam')
    loop.run_until_complete(_())


def test_build_req_and_res(responder, mock_req, mock_res):
    req, res = responder.build_req_and_res()
    assert req is mock_req
    assert res is mock_res


def test_set_request_line(responder, mock_protocol):
    responder.set_request_line('GET', '/', 'HTTP/1.1')
    assert mock_protocol.request['method'] == 'GET'


@pytest.mark.parametrize("prop, proto_prop", [
    ('method', 'client_method'),
    ('parsed_query', 'client_query'),
    ('headers', 'client_headers')
])
def test_forwarded_property(responder, mock_protocol, prop, proto_prop):

    assert getattr(responder, prop) is getattr(mock_protocol, proto_prop)
    setattr(responder, prop, mock.Mock())
    assert getattr(responder, prop) is getattr(mock_protocol, proto_prop)
