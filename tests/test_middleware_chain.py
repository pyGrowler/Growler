#
# tests/test_http_protocol.py
#

import growler
import pytest
from unittest import mock

from test_app import (
    req_uri,
    req,
)


@pytest.fixture
def chain():
    return growler.MiddlewareChain()

@pytest.fixture
def mock_chain():
    return mock.MagicMock(spec=growler.MiddlewareChain,
                          __class__=growler.MiddlewareChain,)


def test_constructor(chain):
    assert isinstance(chain, growler.MiddlewareChain)


def test_add(chain):
    func = mock.Mock()
    chain.add(0x1, '/', func)
    assert func in chain


def test_add_router(chain):
    router = mock.Mock(spec=growler.router.Router)
    chain.add(0x1, '/', router)
    assert router in chain


def test_contains(chain):
    func = mock.Mock()
    chain.add(0x0, '', func)
    assert func in chain


def test_deep_contains(chain):
    inner_chain = growler.MiddlewareChain()
    func = mock.Mock()
    inner_chain.add(0x0, '', func)
    chain.add(0x0, '', inner_chain)
    assert func in chain


@pytest.mark.parametrize('mask, path, reqtuple', [
    (0b01, '/a', (0b01, '/a'))
])
def test_matches_routes(chain, mask, path, reqtuple):
    func = mock.Mock()
    chain.add(mask, path, func)
    for mw in chain(*reqtuple):
        assert mw is func


@pytest.mark.parametrize('mask, path, reqtuple', [
    (0b01, '/a', (0b10, '/a')),
    (0b01, '/a', (0b01, '/b'))
])
def test_not_matches_routes(chain, mask, path, reqtuple):
    func = mock.Mock()
    chain.add(mask, path, func)
    assert len([mw for mw in chain(*reqtuple)]) is 0


@pytest.mark.parametrize('req_uri, middlewares, called', [
    ('/', [mock.Mock(path='/')], [True]),
    ('/a', [mock.Mock(path='/'),
            mock.Mock(path='/a'),
            mock.Mock(path='/b')], [True, True, False]),
    ('/x', [mock.Mock(path='/y'),
            mock.Mock(path='/x/a'),
            mock.Mock(path='/x/a/b/c')], [False, False, False]),
])
def test_handle_client_request_get(chain, req_uri, middlewares, called):
    [chain.add(0x1, mw.path, mw) for mw in middlewares]
    # map(lambda mw: chain.add(0x1, mw.path, mw), middlewares)
    for x in chain(0x1, req_uri):
        x()

    for mw, should_call in zip(middlewares, called):
        if should_call:
            assert mw.called
        else:
            assert mw.not_called
