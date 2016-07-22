#
# tests/test_http_responder.py
#

import growler
from growler.http.responder import GrowlerHTTPResponder
from growler.http.methods import HTTPMethod
from growler.http.errors import HTTPErrorBadRequest
import asyncio
import pytest
from unittest import mock

from mocks import (
    mock_event_loop,
)

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
def mock_protocol(mock_app):
    protocol = mock.Mock(spec=growler.http.protocol.GrowlerHTTPProtocol)
    protocol.socket.getpeername = mock.MagicMock()
    protocol.http_application = mock_app
    protocol.loop = mock_app.loop
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
    assert r.headers == {}


@pytest.mark.parametrize("data", [
    # b'',
    b'GET /',
    b'GET / HTTP/1.1\n',
    b'GET / HTTP/1.1\n\nblahh',
])
def test_on_data_no_headers(responder, mock_parser, data):
    mock_parser.consume.return_value = None
    responder.on_data(data)
    assert responder.headers == {}
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
                              mock_app,
                              data,
                              ):
    # mock_req.body = mock.Mock(spec=asyncio.Future)

    def on_consume(d):
        mock_parser.method = POST
        mock_parser.parsed_url = '/'
        mock_parser.version = 'HTTP/1.1'
        responder.parser.headers = {
            'CONTENT-LENGTH': '%d' % len(data)
        }
        return data

    mock_parser.consume.side_effect = on_consume
    mock_parser.headers = dict()

    responder.on_data(data)

    assert responder.req is mock_req
    assert responder.res is mock_res
    # assert responder.loop.create_task.called
    # responder.app.handle_client_request.assert_called_with(mock_req, mock_res)


@pytest.mark.parametrize("method", [
    (POST),
    (PUT),
])
def test_missing_thing(responder, method):
    with pytest.raises(HTTPErrorBadRequest):
        responder.init_body_buffer(method, {})


@pytest.mark.parametrize("method", [
    (GET),
    (DELETE),
])
def test_missing_thang(responder, method):
    with pytest.raises(HTTPErrorBadRequest):
        responder.init_body_buffer(method, {'CONTENT-LENGTH': 100})


@pytest.mark.parametrize("header", [
])
def test_content_length_wrong_method(responder, header):
    print('')


@pytest.mark.parametrize("data, length", [
    # (b' ' * 10, 100),
    (b'_' * 15, 10),
])
def test_bad_content_length(responder, mock_parser, data, length):
    headers = {'CONTENT-LENGTH': length}
    responder.init_body_buffer(POST, headers)

    with pytest.raises(HTTPErrorBadRequest) as e:
        responder.validate_and_store_body_data(data)
        assert e.value.phrase == "Unexpected body data sent"


@pytest.mark.parametrize("method, request_uri", [
    (GET, '/'),
    (POST, '/foo'),
    (PUT, '/'),
    (DELETE, '/')
])
def test_set_request_line_content_length(responder, method, request_uri):
    responder.set_request_line(method, request_uri, "HTTP/1.1")
    assert responder.parsed_request == (method, request_uri, "HTTP/1.1")
    assert responder.request['method'] == method
    assert responder.request['url'] == request_uri
    assert responder.request['version'] == "HTTP/1.1"


def test_build_req_and_res(responder, mock_req, mock_res):
    req, res = responder.build_req_and_res()
    assert req is mock_req
    assert res is mock_res


def test_set_request_line(responder, mock_protocol):
    responder.set_request_line('GET', '/', 'HTTP/1.1')
    assert responder.request['method'] == 'GET'
    assert responder.request['url'] == '/'
    assert responder.request['version'] == 'HTTP/1.1'


def test_property_method(responder, mock_parser):
    assert responder.method is mock_parser.method


def test_property_method_str(responder, mock_parser):
    assert responder.method_str is mock_parser.method


def test_property_pasred_query(responder, mock_parser):
    assert responder.parsed_query is mock_parser.query


def test_property_headers(responder, mock_parser):
    assert responder.headers is mock_parser.headers


def test_property_loop(responder, mock_protocol, mock_event_loop):
    assert responder.loop is mock_protocol.loop
    assert responder.loop is mock_event_loop


def test_property_app(responder, mock_protocol, mock_app):
    assert responder.app is mock_protocol.http_application
    assert responder.app is mock_app


def test_property_ip(responder, mock_protocol):
    ip = '0.0.0.0'
    mock_protocol.socket.getpeername.return_value = (ip, None)
    assert responder.ip is ip
