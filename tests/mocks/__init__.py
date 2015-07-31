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
