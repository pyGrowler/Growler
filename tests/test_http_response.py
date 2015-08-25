#
# tests/test_http_response.py
#

import growler
import asyncio
import pytest
from unittest import mock

from mock_classes import (                                               # noqa
    request_uri,
)


@pytest.fixture                                                          # noqa
def res(mock_protocol):
    return growler.http.HTTPResponse(mock_protocol)


@pytest.fixture                                                          # noqa
def mock_app():
    return mock.Mock(spec=growler.App,
                     )

@pytest.fixture                                                          # noqa
def mock_protocol(mock_app, request_uri):
    from urllib.parse import (unquote, urlparse, parse_qs)
    parsed_url = urlparse(request_uri)

    protocol = mock.Mock(spec=growler.http.GrowlerHTTPProtocol,
                         loop=mock.Mock(spec=asyncio.BaseEventLoop),
                         http_application=mock_app,
                         headers=None,
                         path=unquote(parsed_url.path),
                         query=parse_qs(parsed_url.query),)

    protocol.socket.getpeername.return_value = ['', '']

    return protocol


def test_constructor(res, mock_protocol):                                # noqa
    assert isinstance(res, growler.http.HTTPResponse)
    assert res.protocol is mock_protocol


def test_construct_with_eol(mock_protocol):                              # noqa
    EOL = ':'
    res = growler.http.HTTPResponse(mock_protocol, EOL)
    assert isinstance(res, growler.http.HTTPResponse)
    assert res.protocol is mock_protocol


def test_default_headers(res):
    res._set_default_headers()
    # assert res.protocol is mock_protocol


def test_send_headers(res):
    res.send_headers()


def test_write(res):
    res.write()


def test_write_eof(res):
    res.write_eof()


def test_end(res):
    res.end()


@pytest.mark.parametrize('url, status', [
    ('/', 200),
])
def test_redirect(res, url, status):
    res.redirect(url, status)
