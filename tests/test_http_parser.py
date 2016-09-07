#
# tests/test_http_parser.py
#

import growler
import growler.http.parser
from growler.http.parser import Parser
from growler.http.methods import HTTPMethod
from growler.http.errors import (
    HTTPErrorBadRequest,
    HTTPErrorInvalidHeader,
    HTTPErrorNotImplemented,
    HTTPErrorVersionNotSupported,
)
import pytest
from urllib.parse import ParseResult
from itertools import zip_longest

from unittest import mock

GET, POST = HTTPMethod.GET, HTTPMethod.POST

from mocks import *                                                      # noqa

from mock_classes import (                                               # noqa
    responder,
    mock_protocol,
    request_uri,
)


@pytest.fixture
def mock_responder():
    return mock.MagicMock(
        spec=growler.http.responder.GrowlerHTTPResponder,
    )


@pytest.fixture
def parser(mock_responder):
    return Parser(mock_responder)

#
# Implementation Specific tests
#

def test_parser_fixture(parser):
    """Asserts the fixture is correct"""
    assert isinstance(parser, Parser)


@pytest.mark.parametrize("data, expected", [
    (b'foo', None),
    (b"a line\n", b'\n'),
    (b"\na line\n", b'\n'),
    (b"another\nline\nhere", b'\n'),
    (b"another\r\nline\r\nhere", b'\r\n'),
])
def test_parser_determine_newline(data, expected):
    val = Parser.determine_newline(data)
    assert val == expected


@pytest.mark.parametrize("line, value", [
    ("GET / HTTP/1.1\n", b'\n'),
    ("GET / HTTP/1.1\r\n", b'\r\n'),
    ("GET / HTTP/1.1", None),
])
def test_aquire_newline_byte_by_byte(line, value, parser):
    assert parser.EOL_TOKEN is None
    for c in line:
        parser.consume(c.encode())
    assert parser.EOL_TOKEN == value


@pytest.mark.parametrize("data, method, path, query, version", [
    ("GET /path HTTP/1.0", GET, '/path', '', 'HTTP/1.0'),
    ("GET /path?tst=T&q=1 HTTP/1.1", GET, '/path', 'tst=T&q=1', 'HTTP/1.1'),
])
def test_store_request_line(data, method, path, query, version, parser):
    m, u, v = parser._store_request_line(data)
    assert m == method
    assert u.path == path
    assert u.query == query
    assert v == version


@pytest.mark.parametrize("data, error_type", [
    ("G\n\n", HTTPErrorBadRequest),
    ("GET /path HTTP/1.2", HTTPErrorVersionNotSupported),
    ("FOO /path HTTP/1.1", HTTPErrorNotImplemented),
])
def test_bad_store_request_line(parser, data, error_type):
    with pytest.raises(error_type):
        parser._store_request_line(data)


@pytest.mark.parametrize("data, method, parsed, version", [
  (b"GET /path HTTP/1.1\n", GET, ('', '', '/path', '', '', ''), 'HTTP/1.1'),
  (b"GET /a#q HTTP/1.1\n", GET, ('', '', '/a', '', '', 'q'), 'HTTP/1.1'),
  (b"POST /p HTTP/1.1\n", POST, ('', '', '/p', '', '', ''), 'HTTP/1.1'),
])
def notest_consume_request_line(parser, data, method, parsed, version):
    parser.consume(data)
    parser.parent.set_request_line.assert_called_with(method,
                                                      ParseResult(*parsed),
                                                      version)


@pytest.mark.parametrize("header_line, expected", [
    (b'the-key: one', ('the-key', 'one')),
])
def test_split_header_key_value(parser, header_line, expected):
    assert parser.split_header_key_value(header_line) == expected


@pytest.mark.parametrize("header_line", [
    b'the-key one',
    b'',
    b'>>:<<',
    b'))<:>((',
    b"host nowhere.com",
    b"host>: nowhere.com",
    b"host?: nowhere.com",
    b":host: nowhere.com",
    # b" host: nowhere.com",
    b"{host}: nowhere.com",
    b"host=true:yes",
    b"andrew@here: good",
    b"b>a:x",
    b"a\\:<",
])
def test_bad_header_key_value(parser, header_line):
    with pytest.raises(HTTPErrorInvalidHeader):
        parser.split_header_key_value(header_line)


@pytest.mark.parametrize("fullreq, expected", [
    (b'GET / HTTP/1.1\nhost:foo\nthe-key: the-value\n\nxyz',
     dict(path='/', method='/', version=('1', '1'), EOL=b'\n', body=b'xyz',
          headers={'THE-KEY': 'the-value', 'HOST': 'foo'})),

    (b'POST / HTTP/1.1\r\nhost: a\r\nm: a\r\n b\r\n   c\r\n\r\n',
     dict(path='/', method='/', version=('1', '1'), EOL=b'\r\n', body=b'',
          headers={'HOST': 'a', 'M': ['a', 'b', 'c']})),

    (b'POST / HTTP/1.1\r\nhost: a\r\nm: a\r\n b\r\n   c\r\n\r\nThis is some body text\r\nWith newlines!!',
     dict(path='/', method='/', version=('1', '1'), EOL=b'\r\n', body=b'This is some body text\r\nWith newlines!!',
          headers={'HOST': 'a', 'M': ['a', 'b', 'c']})),
])
def test_good_request(parser, fullreq, expected):
    body = parser.consume(fullreq)
    assert parser.EOL_TOKEN == expected['EOL']
    assert parser.HTTP_VERSION == expected['version']
    assert parser.path == expected['path']
    assert parser.headers == expected['headers']
    assert body == expected['body']


@pytest.mark.parametrize("req_str, err", [
    (b"GET /somewhere HTTP/1.1\xc3\nheader:true\n\n", HTTPErrorBadRequest),
    (b"OOPS\r\nhost: nowhere.com\r\n", HTTPErrorBadRequest),
    (b"\x99Get Stuff]\n", HTTPErrorBadRequest),
    (b"OOPS /path HTTP/1.1\r\nhost: nowhere.com\r\n", HTTPErrorNotImplemented),
    (b"GET /path HTTP/1.3\r\nhost: nowhere.com\r\n", HTTPErrorVersionNotSupported),
])
def test_bad_request(parser, req_str, err):
    with pytest.raises(err):
        parser.consume(req_str)


def test_request_too_long(parser):
    req_str = b'GET /path HTTP/1.1\n\n' + b'X' * (growler.http.parser.MAX_REQUEST_LENGTH + 4)
    with pytest.raises(HTTPErrorBadRequest):
        parser.consume(req_str)


@pytest.mark.parametrize("header, header_dict", [
    (b"GET / HTTP/1.1\r\nhost: nowhere.com\r\n\r\n",
     {'HOST': 'nowhere.com'}),

    (b"GET /path HTTP/1.1\n\nhost: nowhere.com\n\n",
     dict()),

    (b"GET /path HTTP/1.1\nhost: nowhere.com\n\n",
     {'HOST': 'nowhere.com'}),

    (b"GET /path HTTP/1.1\nhost: nowhere.com\nx:y\n z\n\n",
     {'HOST': 'nowhere.com', 'X': ['y', 'z']}),

])
def test_good_header_all(parser, mock_responder, header, header_dict):
    parser.consume(header)
    assert parser.headers == header_dict


@pytest.mark.timeout(3)
@pytest.mark.parametrize("req_pieces, expected_header", [
    ((b"GET / HTTP/1.1\r\n", b'h:d\r\n\r\n'),
     {'H': 'd'}),

    ((b"GET / ", b"HTTP/1.1\r\n", b'x:y\r\n\r\n'),
     {'X': 'y'}),

    ((b"GET / HTTP/1.1\r\n", b'h:d', b"\r\nhost: now", b"here.com\r\n\r\n"),
     {'HOST': 'nowhere.com', 'H': 'd'}),

    ((b"GET / HTTP/1.1\n", b'h:d', b'\n', b'\ta b\n', b"x:y\n\n"),
     {'X': 'y', 'H': ['d', 'a b']}),

    ((b"GET / HTTP/1.1\n", b'h:d\n', b"host: nowhere.com\n\n"),
     {'HOST': 'nowhere.com', 'H': 'd'}),

    ((b"GET / HTTP/1.1\n", b'A:B\n', b"host: nowhere.com", b"\n\n"),
     {'HOST': 'nowhere.com', 'A': 'B'}),

    ((b"GET / HTTP/1.1\r", b"\nh", b"OsT:  nowhere.com\r", b"\n\r\n"),
     {'HOST': 'nowhere.com'}),
])
def test_good_header_pieces(parser, req_pieces, expected_header):

    for piece in req_pieces:
        parser.consume(piece)

    assert parser.headers == expected_header


@pytest.mark.parametrize("header, parsed, header_dict", [
  ("GET /path HTTP/1.1\r\nhost: nowhere.com\r\n\r\n",
   ('', '', '/path', '', '', ''),
   {'HOST': 'nowhere.com'}),

  ("GET / HTTP/1.1\r\nhost: nowhere.com\r\n\r\n",
   ('', '', '/', '', '', ''),
   {'HOST': 'nowhere.com'}),

])
def test_consume_byte_by_byte(parser, header, parsed, header_dict):
    for c in header:
        parser.consume(c.encode())


@pytest.mark.parametrize("data", [
    '',
])
def test_process_get_headers(parser, data):
    parser.process_get_headers(data)


@pytest.mark.parametrize("data", [
    '',
])
def test_process_post_headers(parser, data):
    parser.process_post_headers(data)
#
# invalid_headers = [
# ]
#
#
# @pytest.mark.parametrize("header", invalid_headers)
# def test_is_invalid_header_name(header):
#     assert Parser.is_invalid_header_name(header) is True
#
#
# @pytest.mark.parametrize("header", list(map(
#     lambda h: "GET /path HTTP/1.1\r\n%s\r\n" % h,
#     invalid_headers
# )))
# def test_invalid_header(parser, header):
#     # with pytest.raises(HTTPErrorInvalidHeader):
#     parser.consume(header.encode())


if __name__ == "__main__":
    test_find_newline()
    # test_store_request_line()
