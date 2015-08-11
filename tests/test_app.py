#
# test_app
#

import asyncio
import pytest
import growler
import types
from unittest import mock

from mocks import *

from mock_classes import (
    MockRequest,
    MockResponse,
    MockProtocol,
)

from test_http_protocol import (
    mock_req as req,
    mock_res as res,
)


@pytest.fixture
def app_name():
    return 'GrowlerApplication'


@pytest.fixture
def router():
    router = mock.Mock(spec=growler.router.Router)
    route_list = []

    router.middleware_chain = lambda req: (yield from route_list)
    router.get = mock.Mock(lambda *args: route_list.append(args))
    return router


@pytest.fixture
def MockProtocol(proto):
    return mock.Mock(return_value=proto)


@pytest.fixture
def proto():
    proto = mock.create_autospec(growler.http.GrowlerHTTPProtocol)
    return proto

@pytest.fixture
def app(app_name, router, mock_event_loop, MockProtocol):
    result = growler.application.Application(app_name,
                                             loop=mock_event_loop,
                                             request_class=MockRequest,
                                             response_class=MockResponse,
                                             protocol_factory=MockProtocol,
                                             )
    result.router = router
    return result


def test_application_constructor():
    app = growler.application.Application('Test')
    assert app.name == 'Test'


def test_application_saves_config():
    val = 'B'
    app = growler.application.Application('Test', A=val)
    assert app.config['A'] is val


def test_application_enables_x_powered_by(app):
    """ Test application enables x-powered-by by default """
    assert app.enabled('x-powered-by')


def test_create_server(app):
    """ Test if the application creates a server coroutine """
    app._protocol_factory = mock.Mock()
    srv = app.create_server()
    assert app.loop.create_server.called
    assert app._protocol_factory.called

def test_create_server_and_run_forever(app):
    print(app.loop)
    app.create_server_and_run_forever()
    assert app.loop.create_server.called
    assert app.loop.run_forever.called


def test_create_server_and_run_forever_args(app):
    app.create_server_and_run_forever(arg1='arg1', arg2='arg2')
    assert app.loop.create_server.called
    assert app.loop.run_forever.called


@pytest.mark.parametrize("method", [
    'get',
    'post',
    'all',
])
def test_forwards_methods(app, router, method):
    do_something = mock.Mock()
    app_method = getattr(app, method)
    app_method('/', do_something)

    router_m = getattr(router, method)
    router_m.assert_called_with('/', do_something)


def test_calling_use(app, router):
    do_something = mock.Mock(spec=types.FunctionType)
    do_something_else = mock.Mock(spec=types.FunctionType)
    app.use(do_something).use(do_something_else)
    assert len(app.middleware) is 2


def test_calling_use_list(app):
    mw_list = (mock.Mock(), mock.Mock(), mock.Mock())
    app.use(mw_list)


def test_use_with_routified_obj(app, router):
    obj = mock.Mock()
    obj.__growler_router = mock.NonCallableMock()
    app.use(obj)
    router.add_router.assert_called_with(None, obj.__growler_router)


def test_use_with_routified_class(app, router):
    sub_router = mock.Mock()
    obj = mock.MagicMock()
    obj.__growler_router.return_value = sub_router
    obj.__growler_router.__class__ = types.MethodType
    app.use(obj)
    router.add_router.assert_called_with(None, sub_router)
    obj.__growler_router.assert_called()


def test_enable(app):
    app.enable('option')
    assert app.enabled('option')


def test_disable(app):
    app.enable('option')
    app.disable('option')
    assert not app.enabled('option')


def test_set_get_del_in_config_item(app):
    obj = mock.MagicMock()
    app['obj'] = obj
    assert app['obj'] is obj
    assert 'obj' in app
    del app['obj']
    assert 'obj' not in app


def test_require(app):
    me = asyncio.Future()
    app.require(me)
    assert me in app._wait_for


def test_empty_middleware_chain(app, req):
    default_middleware = [mw for mw in app.middleware_chain(req)]
    assert len(default_middleware) is 0


def test_middleware_chain_order(app, req):
    middleware = [mock.Mock(), mock.Mock(), mock.Mock(), mock.Mock()]
    app.use(middleware)

    for mw, next_mw in zip(middleware, app.middleware_chain(req)):
        assert mw is next_mw


def test_middleware_chain_router_order(app, router, req):
    middleware = [mock.Mock(), mock.Mock(), mock.Mock(), mock.Mock()]
    # for app.get(None, app.use(middleware)

    for mw, next_mw in zip(middleware, app.middleware_chain(req)):
        assert mw is next_mw


def test_next_error_handler(app):
    for handler in app.next_error_handler():
        assert handler


def test_default_error_handler(app, req, res):
    ex = Exception("boom")
    app.default_error_handler(req, res, ex)
    assert res.send_html.called
