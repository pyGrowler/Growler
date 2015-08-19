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


def test_contains(chain):
    func = mock.Mock()
    chain.add(0x0, '', func)
    assert func in chain


@pytest.mark.parametrize('mask, path, reqtuple', [
    (0b01, '/a', (0b01, '/a'))
])
def test_matches_routes(chain, mask, path, reqtuple):
    func = mock.Mock()
    chain.add(mask, path, func)
    for mw in chain(*reqtuple):
        assert mw.func is func


@pytest.mark.parametrize('mask, path, reqtuple', [
    (0b01, '/a', (0b10, '/a')),
    (0b01, '/a', (0b01, '/b'))
])
def test_not_matches_routes(chain, mask, path, reqtuple):
    func = mock.Mock()
    chain.add(mask, path, func)
    assert len([mw for mw in chain(*reqtuple)]) is 0
