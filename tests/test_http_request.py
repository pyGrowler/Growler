#
# tests/test_http_request.py
#

import pytest
import asyncio
import growler
from inspect import iscoroutine
from growler.http.request import HTTPRequest
from growler.aio.http_protocol import GrowlerHTTPProtocol
from collections import namedtuple
from unittest import mock
from urllib.parse import (
    unquote,
    urlparse,
    parse_qs
)

from mock_classes import (
    request_uri,
)


@pytest.fixture
def mock_protocol(event_loop):
    proto = mock.MagicMock(spec=GrowlerHTTPProtocol)
    proto.loop = event_loop
    return proto


@pytest.fixture
def mock_responder(mock_protocol, event_loop):
    rspndr = mock.MagicMock(spec=growler.http.responder.GrowlerHTTPResponder)
    rspndr._handler = mock_protocol
    rspndr.request = {'url': mock.MagicMock()}
    rspndr.loop = event_loop
    rspndr.body_storage_pair.return_value = (mock.Mock(), mock.Mock())
    return rspndr


@pytest.fixture
def default_headers():
    return {'HOST': 'example.com'}

@pytest.fixture
def empty_req(mock_responder):
    return growler.http.request.HTTPRequest(mock_responder, {})


@pytest.fixture
def get_req(mock_responder, default_headers, request_uri, headers):
    headers.update(default_headers)
    mock_responder.request = {
        'method': "GET",
        'url': mock.Mock(path=request_uri),
        'version': "HTTP/1.1"
    }
    return growler.http.request.HTTPRequest(mock_responder, headers)


@pytest.fixture
def post_req(mock_responder, default_headers, request_uri, headers):
    headers.update(default_headers)
    mock_responder.request = {
        'method': "POST",
        'url': request_uri,
        'version': "HTTP/1.1"
    }
    return growler.http.request.HTTPRequest(mock_responder, headers)


@pytest.mark.parametrize('headers', [
    {},
    {'x': 'x'},
])
def notest_missing_host_request(mock_responder, headers):
    req = HTTPRequest(mock_responder, headers)
    assert req.message


@pytest.mark.parametrize('request_uri, headers, param', [
    ('/', {'x': 'Y'}, ''),
    ('/', {'x': 'x'}, ''),
])
def test_request_headers(get_req, request_uri, headers, param):
    assert get_req.headers['x'] == headers['x']


@pytest.mark.parametrize('request_uri, headers, query', [
    ('/', {}, {}),
    ('/?x=0;p', {}, {'x': ['0']}),
])
def test_query_params(get_req, mock_responder, request_uri, query):
    mock_responder.parsed_query = parse_qs(urlparse(request_uri).query)
    for k, v in query.items():
        assert get_req.param(k) == v


@pytest.mark.asyncio
async def test_construct_with_expected_body(mock_responder):
    BODY = b"""
    here is the text of the body
    """

    async def _body_read():
        return BODY

    async def _body_write():
        return

    mock_responder.body_storage_pair = lambda: (_body_read(), _body_write)
    req = HTTPRequest(mock_responder, {'CONTENT-LENGTH': len(BODY)})

    assert req._body.cr_code is _body_read.__code__

    body = await req.body()
    assert body == BODY

    # getting body
    body = await req.body()
    assert body is BODY


def test_type_is(empty_req, mock_responder):
    a_type = 'http!'
    empty_req.headers['content-type'] = a_type
    assert empty_req.type_is(a_type)


def test_ip_property(empty_req, mock_responder):
    assert empty_req.ip is mock_responder.ip


def test_app_property(empty_req, mock_responder):
    assert empty_req.app is mock_responder.app


def test_path_property(empty_req, mock_responder):
    assert empty_req.path is mock_responder.request['url'].path


def test_original_path_property(empty_req, mock_responder):
    assert empty_req.originalURL is mock_responder.request['url'].path


def test_loop_property(empty_req, event_loop):
    assert empty_req.loop == event_loop


@pytest.mark.parametrize('headers', [
    {'HOST': 'fooo'},
])
def test_hostname_property(get_req, headers):
    assert get_req.hostname == headers['HOST']


def test_method_property(empty_req, mock_responder):
    assert empty_req.method is mock_responder.method


@pytest.mark.parametrize('headers', [{}])
@pytest.mark.parametrize("cipher, expected", [
    (True, 'https'),
    (None, 'http'),
])
def test_protocol_property(get_req, mock_responder, cipher, expected):
    mock_responder.cipher = cipher
    assert get_req.protocol == expected
