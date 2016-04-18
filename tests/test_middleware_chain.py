#
# tests/test_http_protocol.py
#

import growler
from growler.middleware_chain import MiddlewareChain, MiddlewareNode
import pytest
from unittest import mock

from test_app import (
    req_uri,
)


@pytest.fixture
def chain():
    return MiddlewareChain()


@pytest.fixture
def mock_chain():
    return mock.create_autospec(MiddlewareChain)


def test_constructor(chain):
    assert isinstance(chain, MiddlewareChain)


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
    inner_chain = MiddlewareChain()
    func = mock.Mock()
    inner_chain.add(0x0, '', func)
    chain.add(0x0, '', inner_chain)
    assert func in chain


@pytest.mark.parametrize('mask, path, reqtuple', [
    (0b01, '/a', (0b01, '/a')),
])
def test_matches_routes(chain, mask, path, reqtuple):
    func = mock.Mock()
    chain.add(mask, path, func)
    for mw in chain(*reqtuple):
        assert mw is func


@pytest.mark.parametrize('mask, path, reqtuple', [
    (0b01, '/a', (0b10, '/a')),
    (0b01, '/a', (0b01, '/b')),
    (0b01, '/aa', (0b01, '/a')),
    (0b01, '/a', (0b01, '/')),
])
def test_not_matches_routes(chain, mask, path, reqtuple):
    func = mock.Mock()
    chain.add(mask, path, func)
    assert len([mw for mw in chain(*reqtuple)]) is 0


@pytest.mark.parametrize('mw_path, req_match', [
    ('/aa', [('/aa', True), ('/aa/bb', True), ('/bb', False)]),
    ('/aba', [('/aba/', True), ('/abaa', False), ('/aba/a', True)]),
    ('/', [('/', True), ('/a', True)]),
    ('/a', [('/', False), ('/a', True), ('/axb', False), ('/a/b', True)]),
    ('/[x-y]', [('/[x-y]', True), ('/[x-y]/', True), ('/[x-y]/a/c/b', True)]),
])
def test_matching_paths(chain, mw_path, req_match):
    # build middleware from path - add to chain
    mw = mock.MagicMock(path=mw_path)
    chain.add(0x1, mw.path, mw)

    # loop through
    for req_uri, should_match in req_match:

        for x in chain(0x1, req_uri):
            x()
        assert mw.called == should_match, req_uri
        mw.reset_mock()


@pytest.mark.parametrize('mw_path, req_uris', [
    ('/', ['/']),
    ('/a', ['/a/', '/a', '/a/b'],),
    ('/a/c', ['/a/c', '/a/c/', '/a/c/b'],),
    ('/[x-y]', ['/[x-y]', '/[x-y]/', '/[x-y]/a/c/b'],),
])
def test_subchain_matching_paths(chain, mw_path, req_uris):
    # build middleware from path - add to chain
    mw = mock.MagicMock(path=mw_path, spec=MiddlewareChain())
    chain.add(0x1, mw.path, mw)

    # loop through given requests
    for req_uri in req_uris:

        for x in chain(0x1, req_uri):
            x()
        assert mw.called, req_uri
        mw.reset_mock()


@pytest.mark.parametrize('mw_path, req_uris', [
    ('/a', ['/', '/x', '/x/a', '/abc'],),
    ('/a/', ['/a', '/x/a/'],),
])
def test_subchain_not_matching_paths(chain, mw_path, req_uris):
    # build middleware from path - add to chain
    mw = mock.MagicMock(path=mw_path, spec=MiddlewareChain())
    chain.add(0x1, mw.path, mw)

    # loop through
    for req_uri in req_uris:
        for m in chain(0x1, req_uri):
            m()
        assert not mw.called, req_uri
        mw.reset_mock()
