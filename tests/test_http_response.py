#
# tests/test_http_response.py
#

import growler
import asyncio
import pytest
from unittest import mock
from collections import OrderedDict
from growler.http.response import Headers

from mock_classes import (
    request_uri,
)


@pytest.fixture
def res(mock_protocol):
    return growler.http.HTTPResponse(mock_protocol)


@pytest.fixture
def mock_app():
    return mock.Mock(spec=growler.App,
                     )

@pytest.fixture
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


def test_constructor(res, mock_protocol):
    assert isinstance(res, growler.http.HTTPResponse)
    assert res.protocol is mock_protocol


def test_construct_with_eol(mock_protocol):
    EOL = ':'
    res = growler.http.HTTPResponse(mock_protocol, EOL)
    assert isinstance(res, growler.http.HTTPResponse)
    assert res.protocol is mock_protocol
    assert res.EOL is EOL




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


@pytest.mark.parametrize('obj, expect', [
    ({'a': 'b'}, b'{"a": "b"}')
])
def test_json(res, mock_protocol, obj, expect):
    res.json(obj)
    assert res.headers['content-type'] == 'application/json'
    mock_protocol.    transport.write.assert_called_with(expect)


@pytest.mark.parametrize('obj, expect', [
    ({'a': 'b'}, b'{"a": "b"}')
])
def test_headers(res, mock_protocol, obj, expect):
    res.json(obj)
    assert res.headers['content-type'] == 'application/json'
    mock_protocol.transport.write.assert_called_with(expect)


def test_header_construct_with_dict():
    headers = Headers({'a': 'b', 'c': 'D'})
    s = str(headers)
    assert s == 'a: b\r\nc: D\r\n\r\n' or s == 'c: D\r\na: b\r\n\r\n'


def test_header_construct_with_keywords():
    headers = Headers(a='b', c='D')
    s = str(headers)
    assert s == 'a: b\r\nc: D\r\n\r\n' or s == 'c: D\r\na: b\r\n\r\n'


def test_header_construct_mixed():
    headers = Headers({'a': 'b'}, c='D')
    s = str(headers)
    assert s == 'a: b\r\nc: D\r\n\r\n' or s == 'c: D\r\na: b\r\n\r\n'


def test_header_set():
    headers = Headers()
    headers['foo'] = 'bar'
    assert str(headers) == 'foo: bar\r\n\r\n'


def test_header_update_with_dict():
    headers = Headers()
    d = {'foo': 'bar'}
    headers.update(d)
    assert str(headers) == 'foo: bar\r\n\r\n'


def test_header_update_with_multiple_dicts():
    headers = Headers()
    d_0 = OrderedDict([('foo', 'baz'), ('a', 'b')])
    d_1 = {'foo': 'bar'}
    headers.update(d_0, d_1)
    assert str(headers) == 'foo: bar\r\na: b\r\n\r\n'


def test_header_update_with_keyword():
    headers = Headers()
    headers.update(foo='bar')
    assert str(headers) == 'foo: bar\r\n\r\n'


def test_header_update_with_mixed():
    headers = Headers()
    d = {'foo': 'bazz'}
    headers.update(d, foo='bar')
    assert str(headers) == 'foo: bar\r\n\r\n'


def test_callable_header_value():
    headers = Headers()
    headers['foo'] = lambda: 'bar'
    assert str(headers) == 'foo: bar\r\n\r\n'
