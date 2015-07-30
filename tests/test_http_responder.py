#
# tests/test_http_responder.py
#

import growler.http
from growler.http.responder import GrowlerHTTPResponder

import asyncio
import pytest
from unittest.mock import (Mock, MagicMock, create_autospec, patch)

from unittest import mock
from mock_classes import (
    responder,
    mock_protocol,
    request_uri,
)
import mock_classes

# @pytest.fixture
# def mock_protocol():
#     mock_protocol = Mock()
#     mock_protocol.loop = asyncio.get_event_loop()
#     mock_protocol.socket.getpeername.return_value = [1, 3]
#     # mock_protocol.make_responder = responder_factory
#     mock_protocol.request.return_value = ''
#     return mock_protocol
#
#
# @pytest.fixture
# def MockParser():
#     # mock_parser = mock.Mock()
#     # return mock_parser
#
#     def mock_parser(obj):
#         parser = create_autospec(growler.http.Parser(obj))
#         # parser = Mock()
#         parser.consume.return_value = None
#         return parser
#     #     def __init__(self, parent):
#     #         self.parent = parent
#     #         self.i = 0
#     #         self.data = []
#     #
#     #     def consume(self, data, stuff=0):
#     #         if stuff == 0:
#     #             self.parent.set_request_line(data, 2, 3)
#     #         else:
#     #             self.parent.set_headers(data.decode())
#
#     # AutoParser.consume.return_value = None
#     # return mock_parser
#     return patch('growler.http.Parser')


def test_responder_constructor(mock_protocol):
    r = GrowlerHTTPResponder(mock_protocol)
    assert r.loop is mock_protocol.loop
    assert r.headers is None


@pytest.mark.parametrize("data", [
    b'GET / HTTP/1.1\n\nblaahh'
])
def test_on_data(responder, data):
    responder.on_data(data)
    assert responder.headers is None


@pytest.mark.parametrize("method, request_uri, clength", [
    ('GET', '/', None),
    ('POST', '/', 0),
    ('PUT', '/', 0),
    ('DELETE', '/', None)
])
def test_set_request_line_content_length(responder, method, request_uri, clength):
    responder.set_request_line(method, request_uri, "HTTP/1.1")
    assert responder.content_length is clength


def notest_on_parsing_queue(mock_protocol):
    loop = asyncio.get_event_loop()
    r = GrowlerHTTPResponder(mock_protocol, mock_parser)
    r.parsing_task.cancel()

    @asyncio.coroutine
    def _():
        output = yield from r.parsing_queue.get()
        assert output == 'spam'

    r.parsing_queue.put_nowait('spam')
    loop.run_until_complete(_())
