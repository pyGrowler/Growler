#
# tests/mocks/__init__.py
#

import pytest
import asyncio
import socket
import growler
from unittest import mock


@pytest.fixture
def mock_socket():
    """
    returns a mock object with socket.socket interface
    """
    mocksock = mock.Mock(spec=socket.socket)
    return mocksock


@pytest.fixture
def mock_event_loop():
    loop = asyncio.BaseEventLoop()
    return mock.Mock(spec=loop)


@pytest.fixture
def client_port():
    return 2112


@pytest.fixture
def client_host():
    return 'mock.host'


@pytest.fixture
def mock_transport(client_host, client_port):
    transport = mock.Mock(spec=asyncio.WriteTransport)
    transport.get_extra_info.return_value = (client_host, client_port)
    return transport


@pytest.fixture
def mock_router():
    real_router = growler.Router()
    return mock.Mock(spec=real_router)


@pytest.fixture
def mock_req():
    return mock.Mock()
    mock_responder = mock.Mock()
    mock_headers = mock.Mock()
    req = growler.http.HTTPRequest(mock_responder, mock_headers)
    return mock.Mock(spec=req)


@pytest.fixture
def mock_res():
    mock_protocol = mock.Mock()
    res = growler.http.HTTPResponse(mock_protocol)
    return mock.Mock(spec=res)


@pytest.fixture
def mock_req_factory(mock_req):
    factory = mock.Mock(return_value=mock_req)
    return factory


@pytest.fixture
def mock_res_factory(mock_res):
    factory = mock.Mock(return_value=mock_res)
    return factory
