#
# tests/test_http_parser.py
#

from growler.http.parser import Parser

from growler.http.errors import (
    HTTPErrorBadRequest,
    HTTPErrorInvalidHeader,
    HTTPErrorNotImplemented,
    HTTPErrorVersionNotSupported,
)
import pytest


class mock_responder:

    def __init__(self):
        self.data = {}

    def set_request_line(self, method, url, version):
        self.data['method'] = method
        self.data['url'] = url
        self.data['version'] = version

    def set_headers(self, headers):
        self.headers = headers


def pytest_configure(config):
    from pprint import pprint
    print("[pytest_configure]")
    pprint(config)


@pytest.mark.parametrize("line, location, value", [
    (b"a line\n", 6, b'\n'),
    (b"a line\r\n", 6, b'\r\n'),
    (b"no newline", -1, None),
])
def testfind_newline(line, location, value):
    parser = Parser(None)
    assert parser.EOL_TOKEN is None
    assert parser.find_newline(line) == location
    assert parser.EOL_TOKEN == value


@pytest.mark.parametrize("data, method, path, query, version", [
    ("GET /path HTTP/1.0", 'GET', '/path', '', 'HTTP/1.0'),
    ("GET /path?test=true&q=1 HTTP/1.1", 'GET', '/path', 'test=true&q=1', 'HTTP/1.1'),
])
def test_parse_request_line(data, method, path, query, version):
    parser = Parser(None)
    m, u, v = parser.parse_request_line(data)
    assert m == method
    assert u.path == path
    assert u.query == query
    assert v == version


def test_consume():
    q = mock_responder()
    p = Parser(q)
    p.consume(b"GET")
    assert p._buffer == [b"GET"]
    p.consume(b" /path HTTP/1.1")
    p.consume(b"\n")
    data = q.data
    assert data['method'] == 'GET'
    assert data['url'].path == '/path'
    assert data['version'] == 'HTTP/1.1'
    assert not p.needs_request_line

    q2 = mock_responder()
    Parser(q2).consume(b"GET /path HTTP/1.1\nhost: noplace\n\n")
    data = q2.data
    assert data['method'] == 'GET'
    assert data['url'].path == '/path'
    assert data['version'] == 'HTTP/1.1'


@pytest.mark.parametrize("header", [
    b"OOPS\r\nhost: nowhere.com\r\n",
    b"\x99Get Stuff]\n",
])
def test_bad_request(header):
    with pytest.raises(HTTPErrorBadRequest):
        Parser(None).consume(header)


def test_not_implemented():
    with pytest.raises(HTTPErrorNotImplemented):
        Parser(None).consume(b"OOPS /path HTTP/1.1\r\nhost: nowhere.com\r\n")


def test_bad_version():
    with pytest.raises(HTTPErrorVersionNotSupported):
        Parser(None).consume(b"GET /path HTTP/1.3\r\nhost: nowhere.com\r\n")


@pytest.mark.parametrize("header", [
    b"GET / HTTP/1.1\r\nhost: nowhere.com\r\n\r\n",
    b"GET /path HTTP/1.1\nhost: nowhere.com\n\n",
    b"GET /path HTTP/1.1\nhost: nowhere.com\nx:y\n z\n\n",
])
def test_good_header_all(header):
    responder = mock_responder()
    Parser(responder).consume(header)
    headers = responder.headers
    assert 'HOST' in headers
    assert headers['HOST'] == 'nowhere.com'


def test_good_header_pieces():
    q = mock_responder()
    p = Parser(q)
    p.consume(b"GET / HTTP/1.1\r\n")
    p.consume(b"host: nowhere.com\r\n")
    p.consume(b"\r\n")
    headers = q.headers
    assert not p.needs_headers
    assert 'HOST' in headers
    assert headers['HOST'] == 'nowhere.com'
    # assert p.headers['HOST'] == 'nowhere.com'


def test_consume_byte_by_byte():
    responder = mock_responder()
    p = Parser(responder)
    for b in "GET / HTTP/1.1\nhost: nowhere.com\n\n":
        p.consume(b.encode())
    assert not p.needs_headers
    assert 'HOST' in responder.headers
    assert responder.headers['HOST'] == "nowhere.com"


@pytest.mark.parametrize("header", [
    b"GET /path HTTP/1.1\r\nhost nowhere.com\r\n",
    b"GET /path HTTP/1.1\r\nhost>: nowhere.com\r\n",
    b"GET /path HTTP/1.1\r\nhost?: nowhere.com\r\n",
    b"GET /path HTTP/1.1\r\n:host: nowhere.com\r\n",
    b"GET /path HTTP/1.1\r\n host: nowhere.com\r\n"
    b"GET /path HTTP/1.1\r\nhost=true:yes\r\n",
    b"GET /path HTTP/1.1\r\nandrew@here: good\r\n",
    b"GET /path HTTP/1.1\r\nb>a:x\r\n\r\n",
    b"GET /path HTTP/1.1\r\na\\:<\r\n",
])
def test_invalid_header(header):
    with pytest.raises(HTTPErrorInvalidHeader):
        q = mock_responder()
        Parser(q).consume(header)


if __name__ == "__main__":
    testfind_newline()
    # test_parse_request_line()
