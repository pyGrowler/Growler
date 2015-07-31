#
# tests/mocks/__init__.py
#

import pytest
import asyncio
import socket
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
    return mock.Mock(spec=asyncio.BaseEventLoop)


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
