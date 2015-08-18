#
# tests/test_http_protocol.py
#

import growler
import pytest


@pytest.fixture
def chain():
    return growler.MiddlewareChain()


def test_constructor(chain):
    assert isinstance(chain, growler.MiddlewareChain)
