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


@pytest.fixture
def MockResponder():
    MockResponderClass = mock.create_autospec(GrowlerHTTPResponder)

    def build(proto):
        responder = MockResponderClass(proto)
        responder.headers = dict()
        return responder
    return build


@pytest.fixture
def MockProtocol():
    # MockProtocolClass = mock.create_autospec(growler.http.GrowlerHTTPProtocol)

    def MockProtocol(app):
        protocol = mock.patch('growler.http.GrowlerHTTPProtocol')
        print(protocol)
        return protocol
        #
    #     return MockProtocolClass(mock_app)
    return MockProtocol


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
def mock_protocol():
    mock_app = MockApp()
    protocol = MockProtocol()(mock_app)
    protocol.loop = None
    protocol.headers = None
    protocol.http_application = mock_app

    return protocol


@pytest.fixture
def mock_responder():
    # return mock.patch(responder(mock_protocol))
    return MockResponder()(mock_protocol())

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
