#
# tests/mock_classes.py
#
"""
Assembly of mocked up growler classes for use with tests
"""

import pytest
from unittest import mock

import growler
from growler.http.responder import GrowlerHTTPResponder


@pytest.fixture
def MockApp():
    MockAppClass = mock.create_autospec(growler.App)

    def build():
        return MockAppClass()
    return build


@pytest.fixture(scope='session')
def MockResponder():
    MockResponderClass = mock.create_autospec(GrowlerHTTPResponder)

    def buildMockResponder(proto):
        responder = MockResponderClass(proto)
        responder.headers = dict()
        return responder

    return buildMockResponder


@pytest.fixture
def MockProtocol():
    MockProtocolClass = mock.create_autospec(growler.http.GrowlerHTTPProtocol)

    def buildMockProtocol(app):
        protocol = mock.Mock(spec=growler.http.GrowlerHTTPProtocol)
        # protocol = mock.patch('growler.http.GrowlerHTTPProtocol')
        return protocol

    return buildMockProtocol


@pytest.fixture
def MockRequest():
    MockRequestClass = mock.create_autospec(growler.http.request.HTTPRequest)

    def build():
        return MockRequestClass()
    return build


@pytest.fixture
def MockResponse():
    MockResponseClass = mock.create_autospec(growler.http.response.HTTPResponse)

    def build():
        return MockResponseClass()
    return build


@pytest.fixture
def MockParser():
    MockParserClass = mock.create_autospec(growler.http.Parser)

    def generator(a_responder):
        parser = MockParserClass(a_responder)
        parser.consume.return_value = None
        return parser

    return generator


@pytest.fixture
def app():
    return growler.App()


@pytest.fixture
def request_uri():
    return '/'


@pytest.fixture
def mock_protocol(request_uri):
    from urllib.parse import (unquote, urlparse, parse_qs)

    mock_app = MockApp()
    protocol = MockProtocol()(mock_app)
    protocol.loop = None
    protocol.headers = None
    protocol.http_application = mock_app
    protocol.socket.getpeername.return_value = ['', '']

    parsed_url = urlparse(request_uri)
    protocol.path = unquote(parsed_url.path)
    protocol.query = parse_qs(parsed_url.query)

    return protocol


@pytest.fixture
def mock_responder():
    # return mock.patch(responder(mock_protocol))
    return MockResponder()(mock_protocol('/'))

#
# @pytest.fixture
# def responder():
#     from growler.http.responder import GrowlerHTTPResponder
#     Responder = mock.create_autospec(GrowlerHTTPResponder)
#     responder = Responder(protocol())
#     return responder


@pytest.fixture
def responder(mock_protocol):
    return GrowlerHTTPResponder(mock_protocol,
                                parser_factory=MockParser(),
                                request_factory=MockRequest,
                                response_factory=MockResponder)


#
#
# @pytest.fixture
# def mock_parser(responder=None):
#     return MockParser(responder)()


@pytest.fixture
def parser():
    return growler.http.Parser()
