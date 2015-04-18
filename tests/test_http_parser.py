#
# tests/test_http_parser.py
#

import growler

from growler.http.parser import Parser

from growler.http.errors import (
    HTTPErrorBadRequest,
    HTTPErrorInvalidHeader,
    HTTPErrorNotImplemented,
    HTTPErrorVersionNotSupported,
)

import asyncio
# from pytest_localserver import http
import urllib.request

import threading

import socket
import pytest

import warnings


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


def testfind_newline():
    parser = Parser(None)
    assert parser.EOL_TOKEN is None
    assert parser.find_newline(b"a line\n") == 6
    assert parser.EOL_TOKEN == b'\n'

    p2 = Parser(None)
    assert p2.find_newline("a line\r\n") == 6
    assert p2.EOL_TOKEN == b'\r\n'

    p3 = Parser(None)
    assert p2.find_newline('no newline') == -1


def test_parse_request_line():
    parser = Parser(None)
    data = "GET /path?test=true&q=1 HTTP/1.1"
    m, u, v = parser.parse_request_line(data)
    assert m == 'GET'
    assert u.path == '/path'
    assert u.query == 'test=true&q=1'
    assert v == 'HTTP/1.1'


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


def test_bad_request():
    with pytest.raises(HTTPErrorBadRequest):
        Parser(None).consume(b"OOPS\r\nhost: nowhere.com\r\n")

    with pytest.raises(HTTPErrorBadRequest):
        Parser(None).consume(b"\x99Get Stuff]\n")


def test_not_implemented():
    with pytest.raises(HTTPErrorNotImplemented):
        Parser(None).consume(b"OOPS /path HTTP/1.1\r\nhost: nowhere.com\r\n")


def test_bad_version():
    with pytest.raises(HTTPErrorVersionNotSupported):
        Parser(None).consume(b"OOPS /path HTTP/1.3\r\nhost: nowhere.com\r\n")


def test_good_header_all():
    q = mock_responder()
    Parser(q).consume(b"GET / HTTP/1.1\r\nhost: nowhere.com\r\n\r\n")
    headers = q.headers
    assert 'HOST' in headers
    assert headers['HOST'] == 'nowhere.com'

    for valid in [b"GET /path HTTP/1.1\nhost: nowhere.com\n\n",
                  b"GET /path HTTP/1.1\nhost: nowhere.com\nx:y\n z\n\n",
                  ]:
        q = mock_responder()
        Parser(q).consume(valid)


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


def test_bad_headers():
    for invalid in [b"GET /path HTTP/1.1\r\nhost nowhere.com\r\n",
                    b"GET /path HTTP/1.1\r\nhost>: nowhere.com\r\n",
                    b"GET /path HTTP/1.1\r\nhost?: nowhere.com\r\n",
                    b"GET /path HTTP/1.1\r\n:host: nowhere.com\r\n",
                    b"GET /path HTTP/1.1\r\n host: nowhere.com\r\n"
                    b"GET /path HTTP/1.1\r\nhost=true:yes\r\n",
                    b"GET /path HTTP/1.1\r\nandrew@here: good\r\n",
                    b"GET /path HTTP/1.1\r\nb>a:x\r\n\r\n",
                    b"GET /path HTTP/1.1\r\na\\:<\r\n",
                    ]:
        with pytest.raises(HTTPErrorInvalidHeader):
            q = mock_responder()
            Parser(q).consume(invalid)


if __name__ == "__main__":
    testfind_newline()
    # test_parse_request_line()
