#
# tests/test_http_request.py
#

from growler.http.request import HTTPRequest
import pytest
from mock_classes import (
    mock_protocol,
    request_uri,
)

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
    return HTTPRequest(mock_protocol, headers)

@pytest.mark.parametrize('headers', [
    {},
    {'x': 'x'},
])
def test_missing_host_request(mock_protocol, headers):
    with pytest.raises(KeyError):
        HTTPRequest(mock_protocol, headers)


@pytest.mark.parametrize('request_uri, headers, param', [
    ('/', {}, ''),
    ('/', {'x':'x'}, ''),
])
def test_request_something(get_req, param):
    assert get_req.param('x') == param
