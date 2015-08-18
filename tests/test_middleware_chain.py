#
# tests/test_http_protocol.py
#

import growler
import pytest
from unittest import mock

@pytest.fixture
def chain():
    return growler.MiddlewareChain()


def test_constructor(chain):
    assert isinstance(chain, growler.MiddlewareChain)


def test_add(chain):
    func = mock.Mock()
    chain.add(0x1, '/', func)
    assert func in chain
