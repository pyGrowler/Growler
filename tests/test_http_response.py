#
# tests/test_http_response.py
#

import pytest
import random
import growler

from pathlib import Path
from unittest import mock
from asyncio import BaseEventLoop
from collections import OrderedDict
from growler.http.response import Headers

from mock_classes import (
    request_uri,
)


@pytest.fixture
def res(mock_protocol):
    return growler.http.HTTPResponse(mock_protocol)


@pytest.fixture
def headers():
    return Headers()


@pytest.fixture
def mock_app():
    return mock.Mock(spec=growler.App,
                     )

@pytest.fixture
def mock_protocol(mock_app, request_uri):
    from urllib.parse import (unquote, urlparse, parse_qs)
    parsed_url = urlparse(request_uri)

    protocol = mock.Mock(spec=growler.http.GrowlerHTTPProtocol,
                         loop=mock.Mock(spec=BaseEventLoop),
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


def test_set_method(res):
    res.set('a', 'b')
    assert res.get('a') == 'b'


def test_header_method(res):
    res.header('a', 'b')
    assert res.get('a') == 'b'


def test_set_type(res):
    res.set_type('text/x-unknown')
    assert res.headers['content-type'] == 'text/x-unknown'


def test_set_headers_via_dict(res):
    res.set({'a': 'b', 'C': 'd'})
    assert res.get('a') == 'b' # ('a', 'b')
    assert res.get('c') == 'd' # ('C', 'd')
    assert res.get('C') == 'd' # ('C', 'd')


def test_default_headers(res):
    res.get_current_time = 'SPAM'
    res._set_default_headers()
    assert res.headers['Date'] == 'SPAM'
    # assert res.protocol is mock_protocol


def test_send_headers(res):
    res.send_headers()


# def test_set_cookie(res):
#     res.cookie("thing", "value")
#     assert res.cookies["thing"] == "value"
#
#
# def test_clear_cookie(res):
#     res.cookie("thing", "value")
#     assert res.cookies["thing"] == "value"
#     res.remove_cookie("thing")
#     assert 'thing' not in res.cookies
#
#     with pytest.raises(IndexError):
#         res['thing']


def test_links(res):
    res.links({'http://nowhere.nodomain': 'foo'})
    assert res.headers['link'] == '<http://nowhere.nodomain>; rel="foo"'


def test_location(res):
    url = 'http://nowhere.nodomain'
    res.location(url)
    assert res.headers['Location'] == url


def test_response_info_propery(res):
    assert res.info is res.SERVER_INFO


def test_send_headers_with_callback_event(res):
    h = mock.Mock()
    w = mock.Mock()
    res.events.on('headers', h)
    res.send_headers()
    assert h.called
    assert not w.called


def test_send(res, mock_protocol):
    with pytest.raises(NotImplementedError):
        res.send()
    return


def test_write(res, mock_protocol):
    res.write()
    mock_protocol.transport.write.assert_called_with(b'')
    mock_protocol.transport.write_eof.assert_not_called()


def test_write_eof(res, mock_protocol):
    res.write_eof()
    mock_protocol.transport.write_eof.assert_called_with()
    assert not mock_protocol.transport.write.called


def test_write_eof_with_callback_event(res, mock_protocol):
    h = mock.Mock()
    w = mock.Mock()
    res.events.on('after_send', w)
    res.write_eof()
    assert not h.called
    assert w.called

    mock_protocol.transport.write_eof.assert_called_with()
    assert not mock_protocol.transport.write.called


def test_end(res, mock_protocol):
    res.end()
    assert res.has_ended

    written_bytes = mock_protocol.transport.write.call_args_list[0][0][0]
    assert written_bytes.startswith(b"HTTP/1.1 200 OK\r\n")


@pytest.mark.parametrize('url, status', [
    ('/', None),
    ('/to/somewhere', None),
    ('http://a.remote.server/with/path', None),
    ('/', 200),
])
def test_redirect(res, mock_protocol, url, status):
    res.redirect(url, status)
    write = mock_protocol.transport.write
    assert write.call_count == 2

    # get the bytes written to transport
    written_bytes = write.call_args_list[0][0][0]

    # check status code
    expected_status = b'302' if status is None else ('%d' % status).encode()
    assert written_bytes.startswith(b"HTTP/1.1 " + expected_status)

    # check location header
    locate_header = ('\nlocation: %s\r\n' % url).encode()
    assert locate_header in written_bytes

    # never have a content length
    assert b'\r\nContent-Length: 0\r\n' in written_bytes
    assert written_bytes.endswith(b'\r\n\r\n')

    body_bytes = mock_protocol.transport.write.call_args_list[1][0][0]
    assert body_bytes is b''


@pytest.mark.parametrize('obj, expect', [
    ({'a': 'b'}, b'{"a": "b"}'),
    ({'x': [1, 2., 3]}, b'{"x": [1, 2.0, 3]}'),
    ("spamalot!", b'"spamalot!"'),
])
def test_json(res, mock_protocol, obj, expect):
    res.json(obj)
    assert res.headers['content-type'] == 'application/json'

    header_bytes = mock_protocol.transport.write.call_args_list[0][0][0]
    assert b'application/json' in header_bytes

    # mock_protocol.transport.write.assert_called_with(expect)
    body_bytes = mock_protocol.transport.write.call_args_list[1][0][0]
    assert body_bytes == expect

def test_send_html(res, mock_protocol):
    data = "<html><head></head><body>This is just some dummy text</body></html>"
    size = len(data)
    res.send_html(data)
    assert res.headers['content-type'] == 'text/html'

    header_bytes = mock_protocol.transport.write.call_args_list[0][0][0]

    length_header = ('\r\nContent-Length: %d\r\n' % size).encode()
    assert length_header in header_bytes
    assert b'\r\nContent-Type: text/html\r\n' in header_bytes

    body_bytes = mock_protocol.transport.write.call_args_list[1][0][0]
    assert body_bytes == data.encode()


def test_send_file(res, mock_protocol, tmpdir):
    # random_bytes = bytes(random.getrandbits(8) for _ in range(128))
    random_bytes = (b'Hello world! this is the contents of the file '
                    b'which will be sent by the server\n'
                    b'how neat is THAT!?!')
    size = len(random_bytes)
    filename = "testfile.bin"
    f = tmpdir.join(filename)
    f.write(random_bytes)

    res.send_file(str(tmpdir / filename))

    body_bytes = mock_protocol.transport.write.call_args_list[1][0][0]
    assert body_bytes == random_bytes

    header_bytes = mock_protocol.transport.write.call_args_list[0][0][0]
    length_header = ('\r\nContent-Length: %d\r\n' % size).encode()
    assert length_header in header_bytes


def test_send_file_by_path_object(res, mock_protocol, tmpdir):
    data = b'spam-spam-spam'
    f = tmpdir / 'spam.txt'
    f.write(data)

    res.send_file(Path(str(f)))

    body_bytes = mock_protocol.transport.write.call_args_list[1][0][0]
    assert body_bytes == data


@pytest.mark.parametrize('obj, expect', [
    ({'a': 'b'}, b'{"a": "b"}')
])
def test_headers(res, mock_protocol, obj, expect):
    res.json(obj)
    assert res.headers['content-type'] == 'application/json'
    mock_protocol.transport.write.assert_called_with(expect)


def test_header_fixture(headers):
    assert isinstance(headers, Headers)


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


def test_header_set(headers):
    headers['foo'] = 'bar'
    assert str(headers) == 'foo: bar\r\n\r\n'

def test_header_del(headers):
    headers['foo'] = 'bar'
    assert str(headers) == 'foo: bar\r\n\r\n'

    del headers['Foo']
    assert str(headers) == '\r\n\r\n'


def test_header_update_with_dict(headers):
    d = {'foo': 'bar'}
    headers.update(d)
    assert str(headers) == 'foo: bar\r\n\r\n'


def test_header_update_with_multiple_dicts(headers):
    d_0 = OrderedDict([('foo', 'baz'), ('a', 'b')])
    d_1 = {'foo': 'bar'}
    headers.update(d_0, d_1)
    assert str(headers) == 'foo: bar\r\na: b\r\n\r\n'


def test_header_update_with_keyword(headers):
    headers.update(foo='bar')
    assert str(headers) == 'foo: bar\r\n\r\n'


def test_header_update_with_mixed(headers):
    d = {'foo': 'bazz'}
    headers.update(d, foo='bar')
    assert str(headers) == 'foo: bar\r\n\r\n'


def test_callable_header_value(headers):
    headers['foo'] = lambda: 'bar'
    assert str(headers) == 'foo: bar\r\n\r\n'


def test_headers_dequote():
    assert Headers.de_quote('foo"bar') == r'foo\"bar'


def test_headers_add_header(headers):
    headers.add_header('A', 'b')
    assert headers['a'] == 'b'
    assert str(headers).encode() == b"A: b\r\n\r\n"


def test_headers_add_header_list(headers):
    headers.add_header('A', ['a', 'b', 'c'])
    assert str(headers) == 'A: a\r\n\tb\r\n\tc\r\n\r\n'


def test_headers_add_header_tuple(headers):
    headers.add_header('A', ('a', 'b', 'c'))
    assert str(headers) == 'A: a\r\n\tb\r\n\tc\r\n\r\n'


def test_headers_add_header_with_params(headers):
    headers.add_header('A', 'b', encoding='utf8', foo='bar')
    assert str(headers) == 'A: b; encoding="utf8" foo="bar"\r\n\r\n'
