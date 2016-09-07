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


def test_chain_fixture(chain):
    assert isinstance(chain, MiddlewareChain)


def test_chain_add_middleware(chain):
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


def test_chain_calls_iterate_subchain(chain):
    mw0 = lambda x, y: None
    mw1 = lambda x, y: None
    mw2 = lambda x, y: None
    chain.add(1, '/', mw0)
    chain.add(1, '/', mw1)
    chain.add(1, '/', mw2)
    gen = chain(1, '/')
    assert next(gen) is mw0
    assert next(gen) is mw1
    assert next(gen) is mw2


def test_chain_calls_iterate_subchain(chain):
    mw = lambda x, y: None
    mw0 = lambda x, y: None
    mw1 = lambda x, y: None
    mw2 = lambda x, y: None
    mw3 = lambda x, y: None
    mock_chain0 = mock.MagicMock(spec=chain, return_value=[mw0])
    mock_chain1 = mock.MagicMock(spec=chain, return_value=[mw2])
    mock_chain2 = mock.MagicMock(spec=chain, return_value=[mw3])
    chain.add(1, '/', mw)
    chain.add(1, '/', mock_chain0)
    chain.add(2, '/', mock_chain1)
    chain.add(1, '/foo', mock_chain2)
    chain.add(1, '/', mw3)

    gen = chain(1, '/')
    assert next(gen) is mw
    assert next(gen) is mw0
    assert next(gen) is mw3

    mock_chain0.assert_called_once_with(1, '/')
    assert not mock_chain1.called
    assert not mock_chain2.called


def test_chain_adds_error_handler(chain):
    eh = lambda x, y, z: None
    chain.add('', '/', eh)
    last_mw = chain.mw_list[-1]

    assert last_mw.func is eh
    assert last_mw.is_errorhandler


def test_chain_calls_error_handler(chain):
    ex = Exception("boom")
    e_mw = mock.MagicMock(side_effect=ex)

    m = mock.MagicMock()
    eh0 = lambda x, y, z: m(x, y, z)
    eh1 = lambda x, y, z: m(x, y, z)

    chain.add(0x1, '/', eh0)
    chain.add(0x1, '/', eh1)
    chain.add(0x1, '/', e_mw)

    gen = chain(0x1, '/')
    gen_mw = next(gen)
    assert gen_mw is e_mw

    gen.throw(ex)
    err_handler = next(gen)
    assert err_handler is eh1

    err_handler = next(gen)
    assert err_handler is eh0

    with pytest.raises(StopIteration):
        next(gen)


def test_chain_handles_error_in_error(chain):

    handler = chain.handle_error(None, [None])
    next(handler)
    assert handler.throw(Exception("boom")) is None


def test_terate_subchain_handles_error(chain):
    m = mock.MagicMock()
    e = Exception("boom")

    def sub_chain():
        try:
            yield m
        except Exception as err:
            assert err is e
            yield

    gen = chain.iterate_subchain(sub_chain())
    assert next(gen) is m
    gen.throw(e)


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


def test_count_all(chain):
    m = MiddlewareChain()
    m.add(0, 0, mock.MagicMock())
    m.add(0, 0, mock.MagicMock())
    m.add(0, 0, mock.MagicMock())

    n = MiddlewareChain()
    n.add(0, 0, mock.MagicMock())
    n.add(0, 0, mock.MagicMock())

    chain.add(0, '/', m)
    chain.add(0, 0, mock.MagicMock())
    chain.add(0, 0, n)

    assert chain.count_all() == 6


def test_chain_reversed(chain):
    # build middleware from path - add to chain
    mw0 = mock.MagicMock() # path=mw_path, spec=MiddlewareChain())
    mw1 = mock.MagicMock()
    chain.add(0x1, '/', mw0)
    chain.add(0x1, '/', mw1)

    rev = reversed(chain)
    assert next(rev).func is mw1
    assert next(rev).func is mw0
