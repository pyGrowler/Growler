#
# tests/test_http_request.py
#

import growler
from growler.http.request import HTTPRequest
import pytest
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
def mock_protocol():
    proto = mock.MagicMock(spec=growler.http.protocol.GrowlerHTTPProtocol)
    return proto


@pytest.fixture
def default_headers():
    return {'HOST': 'example.com'}


@pytest.fixture
def get_req(mock_protocol, default_headers, request_uri, headers):
    headers.update(default_headers)
    mock_protocol.request = {
        'method': "GET",
        'url': request_uri,
        'version': "HTTP/1.1"
    }
    return growler.http.request.HTTPRequest(mock_protocol, headers)


@pytest.fixture
def post_req(mock_protocol, default_headers, request_uri, headers):
    headers.update(default_headers)
    mock_protocol.request = {
        'method': "POST",
        'url': request_uri,
        'version': "HTTP/1.1"
    }
    return growler.http.request.HTTPRequest(mock_protocol, headers)


@pytest.mark.parametrize('headers', [
    {},
    {'x': 'x'},
])
def notest_missing_host_request(mock_protocol, headers):
    req = HTTPRequest(mock_protocol, headers)
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
def test_query_params(get_req, mock_protocol, request_uri, query):
    mock_protocol.client_query = parse_qs(urlparse(request_uri).query)
    for k, v in query.items():
        assert get_req.param(k) == v
