#
# tests/test_http_parser.py
#

import growler
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
            spec=growler.http.responder.GrowlerHTTPResponder
           )


@pytest.fixture
def parser(mock_responder):
    return Parser(mock_responder)


@pytest.mark.parametrize("line, location, value", [
    (b"a line\n", 6, b'\n'),
    (b"a line\r\n", 6, b'\r\n'),
    (b"no newline", -1, None),
])
def test_find_newline(line, location, value, parser):
    assert parser.EOL_TOKEN is None
    assert parser.find_newline(line) == location
    assert parser.EOL_TOKEN == value


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
def test_parse_request_line(data, method, path, query, version, parser):
    m, u, v = parser.parse_request_line(data)
    assert m == method
    assert u.path == path
    assert u.query == query
    assert v == version


def test_consume_buffer(parser):
    parser.consume(b"GET")
    assert parser._buffer == [b"GET"]


@pytest.mark.parametrize("data, method, parsed, version", [
  (b"GET /path HTTP/1.1\n", GET, ('', '', '/path', '', '', ''), 'HTTP/1.1'),
  (b"GET /a#q HTTP/1.1\n", GET, ('', '', '/a', '', '', 'q'), 'HTTP/1.1'),
  (b"POST /p HTTP/1.1\n", POST, ('', '', '/p', '', '', ''), 'HTTP/1.1'),
])
def test_consume_request_line(parser, data, method, parsed, version):
    parser.consume(data)
    parser.parent.set_request_line.assert_called_with(method,
                                                      ParseResult(*parsed),
                                                      version)


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


@pytest.mark.parametrize("header, header_dict", [
    (b"GET / HTTP/1.1\r\nhost: nowhere.com\r\n\r\n",
     {'HOST': 'nowhere.com'}),

    (b"GET /path HTTP/1.1\nhost: nowhere.com\n\n",
     {'HOST': 'nowhere.com'}),

    (b"GET /path HTTP/1.1\nhost: nowhere.com\nx:y\n z\n\n",
     {'HOST': 'nowhere.com', 'X': ['y', 'z']}),

])
def test_good_header_all(parser, mock_responder, header, header_dict):
    # Parser(mock_responder).consume(header
    parser.consume(header)
    print(mock_responder.mock_calls)
    assert mock_responder.headers == header_dict


@pytest.mark.parametrize("header_pieces, header_d", [
    ((b"GET / HTTP/1.1\r\n", b"host: nowhere.com\r\n", b"\r\n"),
     {'HOST': 'nowhere.com'}),

    ((b"GET / HTTP/1.1\r", b"\nh", b"OsT:  nowhere.com\r", b"\n\r\n"),
     {'HOST': 'nowhere.com'}),
])
def test_good_header_pieces(parser, mock_responder, header_pieces, header_d):

    for piece in header_pieces:
        parser.consume(piece)

    assert mock_responder.headers == header_d


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

    parser.parent.set_request_line.assert_called_with(HTTPMethod.GET,
                                                      ParseResult(*parsed),
                                                      'HTTP/1.1')


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
def test_invalid_header(responder, header):
    with pytest.raises(HTTPErrorInvalidHeader):
        Parser(responder).consume(header)


if __name__ == "__main__":
    test_find_newline()
    # test_parse_request_line()
