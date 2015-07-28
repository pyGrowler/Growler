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
from urllib.parse import ParseResult
from unittest import mock
from unittest.mock import (ANY, Mock)

from mock_classes import (
    responder,
    mock_protocol,
    mock_responder,
)


@pytest.fixture
def parser(mock_responder):
    return Parser(mock_responder)


# def responder():
#     from growler.http.responder import GrowlerHTTPResponder
#     Responder = mock.create_autospec(GrowlerHTTPResponder)
#     responder = Responder()
#     print("responder.headers", responder.headers)
#     # responder.headers = dict()
#     # def set_headers(headers):
#         # responder.headers = headers
#     # responder.set_headers = set_headers
#     return responder
#     # return Mock(mock_responder())


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


def test_consume(parser):
    parser.consume(b"GET")
    assert parser._buffer == [b"GET"]
    parser.consume(b" /path HTTP/1.1")
    parser.consume(b"\n")
    p = ParseResult('', '', '/path', '', '', '')
    parser.parent.set_request_line.assert_called_with('GET',
                                                      p,
                                                      'HTTP/1.1')


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
def test_good_header_all(parser, header, header_dict):
    # Parser(mock_responder).consume(header
    parser.consume(header)
    parser.parent.set_headers.assert_called_with(header_dict)


@pytest.mark.parametrize("header_pieces, headers_set", [
    ((b"GET / HTTP/1.1\r\n", b"host: nowhere.com\r\n", b"\r\n"),
     {'HOST': 'nowhere.com'}),

    ((b"GET / HTTP/1.1\r\n", b"hOsT:  nowhere.com\r\n", b"\r\n"),
     {'HOST': 'nowhere.com'}),
])
def test_good_header_pieces(parser, header_pieces, headers_set):

    for piece in header_pieces:
        parser.consume(piece)

    parser.parent.set_headers.assert_called_with(headers_set)

    # headers = mock_responder.headers
    # assert not parser.needs_headers
    # assert 'HOST' in headers
    # assert headers['HOST'] == 'nowhere.com'
    # assert p.headers['HOST'] == 'nowhere.com'


@pytest.mark.parametrize("header, header_dict", [
    ("GET / HTTP/1.1\r\nhost: nowhere.com\r\n\r\n",
     {'HOST': 'nowhere.com'}),
])
def test_consume_byte_by_byte(header, header_dict, parser):
    # for c in header:
    #     print("c", c)
    #     parser.consume(c.encode())

    map(parser.consume, [c.encode() for c in header])
    expected_result = ParseResult('', '', '/path', '', '', '')
    # parser.parent.set_request_line.assert_called_with('GET',
    #                                                   expected_result,
    #                                                   'HTTP/1.1')
    # parser.parent.set_headers.assert_called_with(header_dict)
    assert not parser.needs_headers
    # assert responder.headers.get('HOST') == "nowhere.com"


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
    testfind_newline()
    # test_parse_request_line()
