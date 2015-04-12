#
# tests/test_http_parser.py
#

import growler

from growler.http.parser import Parser

from growler.http.Error import HTTPErrorNotImplemented

import asyncio
# from pytest_localserver import http
import urllib.request

import threading

import socket
import pytest

def pytest_configure(config):
    from pprint import pprint
    print("[pytest_configure]")
    pprint(config)

def test_find_newline():
    parser = Parser(None)
    assert parser._find_newline("a line\n") == 6
    assert parser.EOL_TOKEN == '\n'

    p2 = Parser(None)
    assert p2._find_newline("a line\r\n") == 6
    assert p2.EOL_TOKEN == '\r\n'

    p3 = Parser(None)
    assert p2._find_newline('no newline') == -1

def test_parse_request_line():
    parser = Parser(None)
    data = "GET /path?test=true&q=1 HTTP/1.1"
    m, u, v = parser.parse_request_line(data)
    assert m == 'GET'
    assert u.path == '/path'
    assert u.query == 'test=true&q=1'
    assert v == 'HTTP/1.1'
    print(u)

def test_consume():
    class mock_queue:
        data = None
        def put_nowait(self, data):
            self.data = data
    q = mock_queue()
    p = Parser(q)
    p.consume(b"GET")
    assert p._buffer == ["GET"]
    p.consume(b" /path HTTP/1.1")
    p.consume(b"\n")
    assert q.data['method'] == 'GET'
    assert q.data['url'].path == '/path'
    assert q.data['version'] == 'HTTP/1.1'

    p2 = Parser(q)
    p2.consume(b"GET /path HTTP/1.1\nhost: noplace\n\n")
    assert q.data['method'] == 'GET'
    assert q.data['url'].path == '/path'
    assert q.data['version'] == 'HTTP/1.1'

def test_bad_request():
    with pytest.raises(HTTPErrorNotImplemented):
        p = Parser(None)
        data = b"""OOPS /path HTTP/1.1\r\nhost: nowhere.com\r\n"""
        p.consume(data)

# test_bad_request()
test_parse_request_line()
