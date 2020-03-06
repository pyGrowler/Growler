#
# test_app
#

import re
import sys
import types
import pytest
from asyncio.coroutines import iscoroutine

from mocks import *                                                      # noqa
from unittest import mock
from growler import growler, Application, GrowlerStopIteration


from mock_classes import (
    MockRequest,
    MockResponse,
    MockProtocol,
)

from test_http_protocol import (
    mock_res as res,
)


@pytest.fixture
def app_name():
    return 'GrowlerApplication'


@pytest.fixture
def router():
    return mock.Mock(spec=growler.Router,
                     middleware_chain=lambda req: (yield from ()),
                     get=mock.Mock(lambda *args: route_list.append(args)))


@pytest.fixture
def mock_MiddlewareChain():
    return mock.create_autospec(growler.MiddlewareChain)

@pytest.fixture
def use_mock_middlewarechain():
    return False

@pytest.fixture
def proto():
    proto = mock.create_autospec(growler.http.GrowlerHTTPProtocol)
    return proto


@pytest.fixture
def req_uri():
    return '/'


@pytest.fixture
def req(req_uri):
    return mock.Mock(spec=growler.http.HTTPRequest,
                     path=req_uri,
                     method=0x01)


@pytest.fixture
def app(app_name, mock_MiddlewareChain, use_mock_middlewarechain, MockProtocol):

    mw_chain = mock_MiddlewareChain if use_mock_middlewarechain else None
    result = Application(app_name,
                         request_class=MockRequest,
                         response_class=MockResponse,
                         middleware_chain=mw_chain)
    return result


@pytest.fixture
def app_with_router(app, router):
    app.middleware.add(growler.http.methods.HTTPMethod.ALL, '/', router)
    return app


def test_application_constructor():
    app = growler.Application('Test')
    assert app.name == 'Test'


def test_application_constructor_alternate_middleware_type():
    app = growler.Application('Test', middleware_chain=list)
    assert app.middleware == []


@pytest.mark.parametrize("use_mock_middlewarechain", [True])
def test_app_fixture(app, app_name, mock_MiddlewareChain, MockProtocol):
    assert isinstance(app, growler.Application)
    assert app.middleware is mock_MiddlewareChain
    assert app._request_class is MockRequest
    assert app._response_class is MockResponse


def test_application_saves_config():
    val = 'B'
    app = growler.Application('Test', A=val)
    assert app.config['A'] is val


def test_application_enables_x_powered_by(app):
    """ Test application enables x-powered-by by default """
    assert app.enabled('x-powered-by')


def test_all(app_with_router, router):
    m = mock.Mock()
    app_with_router.all('/', m)
    router.all.assert_called_with('/', m)


def test_get(app_with_router, router):
    m = mock.Mock()
    app_with_router.get('/', m)
    router.get.assert_called_with('/', m)


def test_post(app_with_router, router):
    m = mock.Mock()
    app_with_router.post('/', m)
    router.post.assert_called_with('/', m)


def test_put(app_with_router, router):
    m = mock.Mock()
    app_with_router.put('/', m)
    router.put.assert_called_with('/', m)


def test_delete(app_with_router, router):
    m = mock.Mock()
    app_with_router.delete('/', m)
    router.delete.assert_called_with('/', m)


def test_use_function(app, mock_route_generator):
    m = mock_route_generator()
    app.use(m)
    assert app.middleware.last().func is m


def test_use_tuple(app, mock_route_generator):
    mws = tuple(mock_route_generator() for i in range(3))
    app.use(mws)
    assert len(mws) is len(app.middleware.mw_list)
    assert all((a.func is b for a, b in zip(app.middleware.mw_list, mws)))


def test_use_list(app, mock_route_generator):
    mw_list = [mock_route_generator() for i in range(3)]
    app.use(mw_list)
    assert len(mw_list) is len(app.middleware.mw_list)
    assert all((a.func is b for a, b in zip(app.middleware.mw_list, mw_list)))


def test_use_growler_router(app, mock_route_generator):
    m = mock.Mock()
    route = mock_route_generator()
    m.__growler_router = route
    app.use(m)
    assert app.middleware.last().func is route


def test_use_growler_router_factory(app, mock_route_generator):
    router = mock_route_generator()
    m = mock.Mock()
    m.__growler_router = mock.Mock(spec=types.MethodType,
                                   return_value=router)
    app.use(m)
    assert m.__growler_router.called
    assert app.middleware.last().func is router


def test_use_as_decorator(app):

    @app.use
    def test_mw(req, res):
        pass

    assert test_mw is not app
    assert app.middleware.last().func is test_mw
    assert app.middleware.last().path is growler.MiddlewareChain.ROOT_PATTERN


def test_use_as_called_decorator(app):

    @app.use(path='/foo')
    def test_mw(req, res):
        pass

    assert test_mw is not app
    assert app.middleware.last().func is test_mw
    assert app.middleware.last().path == re.compile(re.escape('/foo'))


def test_add_bad_router(app):
    # TODO: Implement real check for router type
    app.strict_router_check = True
    with pytest.raises(TypeError):
        app.add_router("/foo", lambda req, res: res.send_text("bad type!"))


def test_ignore_add_bad_router(app):
    app.strict_router_check = False
    app.add_router("/foo", lambda req, res: res.send_text("bad type!"))


def test_use_growler_router_metaclass(app, mock_route_generator):

    class TestMeta(metaclass=growler.RouterMeta):

        def get_z(self, req, res): '''/'''
        def get_a(self, req, res): '''/a/a'''
        def get_b(self, req, res): '''/a/b'''

    mrouter = TestMeta()
    app.use(mrouter)
    router = app.middleware.mw_list[0].func

    assert isinstance(router, growler.Router)
    assert mrouter.get_z == router.mw_list[0].func
    assert mrouter.get_a == router.mw_list[1].func
    assert mrouter.get_b == router.mw_list[2].func


def test_create_server_return_server(app, event_loop, unused_tcp_port):
    """ Test if the application creates a server coroutine """
    from asyncio.base_events import Server
    proto_factory = mock.Mock()
    server_cfg = dict(host='localhost', port=unused_tcp_port)

    server = app.create_server(proto_factory,
                               loop=event_loop,
                               as_coroutine=False,
                               **server_cfg)

    assert isinstance(server, Server)
    if hasattr(server, '_protocol_factory'):
        assert server._protocol_factory is proto_factory.return_value


@pytest.mark.asyncio
async def test_create_server_return_coroutine(app, event_loop, unused_tcp_port):
    from unittest.mock import MagicMock
    from asyncio.base_events import Server
    """ Test if the application creates a server coroutine """
    proto_factory = mock.Mock()
    server_config = dict(host='127.1', port=unused_tcp_port)
    server_coroutine = app.create_server(proto_factory,
                                         as_coroutine=True,
                                         **server_config)

    assert iscoroutine(server_coroutine)
    server = await server_coroutine
    assert isinstance(server, Server)
    if hasattr(server, '_protocol_factory'):
        assert server._protocol_factory is proto_factory.return_value
    proto_factory.assert_called_with(app)


def test_create_server_default_params(app, event_loop, unused_tcp_port):
    """ Test if the application creates a server coroutine """
    from asyncio.base_events import Server
    asyncio.set_event_loop(event_loop)
    server = app.create_server(port=unused_tcp_port, host='localhost')
    assert isinstance(server, Server)
    assert server._loop is event_loop

    # create_server_call = mock.call(mock.ANY, port=1)
    # assert mock_event_loop.create_server.mock_calls[0] == create_server_call

    # run_until_complete_call = mock.call(mock_event_loop.create_server.return_value)
    # assert mock_event_loop.run_until_complete.mock_calls[0] == run_until_complete_call


def test_create_server_and_run_forever(app):
    mock_protocol_factory = mock.Mock()
    mock_event_loop = mock.MagicMock()
    mock_server_coro = mock.Mock()
    mock_event_loop.create_server.return_value = mock_server_coro

    host = mock.Mock()
    port = mock.Mock()
    app.create_server_and_run_forever(loop=mock_event_loop,
                                      protocol_factory=mock_protocol_factory,
                                      host=host,
                                      port=port)

    mock_protocol_factory.assert_called_once_with(app)
    mock_event_loop.create_server.assert_called_with(mock_protocol_factory.return_value,
                                                     host=host,
                                                     port=port)
    mock_event_loop.run_forever.assert_called_once()
    mock_event_loop.run_until_complete.assert_called_once_with(mock_server_coro)


def test_create_server_and_run_forever_default_params(app):
    """ Test if the application creates a server """
    import asyncio

    mock_event_loop = mock.Mock(spec=asyncio.AbstractEventLoop)

    # solves a coverage problem
    mock_event_loop.run_forever.side_effect = KeyboardInterrupt

    asyncio.set_event_loop(mock_event_loop)

    mock_server = mock.Mock()
    mock_event_loop.create_server = mock.MagicMock(return_value=mock_server)

    protocol_path = "growler.aio.GrowlerHTTPProtocol.get_factory"
    with mock.patch(protocol_path) as mock_get_factory:
        noval = app.create_server_and_run_forever(host='◉', port=1)

    assert noval is None
    mock_event_loop.create_server.assert_called_once_with(mock_get_factory.return_value,
                                                          host='◉',
                                                          port=1)
    mock_event_loop.run_until_complete.assert_called_once_with(mock_server)
    mock_event_loop.run_forever.assert_called_with()


# @pytest.mark.parametrize("method", [
#     'get',
#     'post',
#     'all',
# ])
# def test_forwards_methods(app, router, method):
#     do_something = mock.Mock()
#     app_method = getattr(app, method)
#     app_method('/', do_something)
#
#     router_m = getattr(router, method)
#     router_m.assert_called_with('/', do_something)


# def test_calling_use(app, router):
#     do_something = mock.Mock(spec=types.FunctionType)
#     do_something_else = mock.Mock(spec=types.FunctionType)
#     app.use(do_something).use(do_something_else)
#     assert len(app.middleware) is 2


@pytest.fixture
def mock_route_generator():
    return lambda: mock.create_autospec(lambda rq, rs: None)

def test_fixture_mock_event_loop(mock_event_loop):
    assert isinstance(mock_event_loop, asyncio.AbstractEventLoop)

def test_fixture_app(app: Application, mock_event_loop):
    assert isinstance(app, Application)
    assert len(app.middleware.mw_list) is 0


def test_router_property(app):
    app.router
    assert len(app.middleware.mw_list) is 1


# def test_use_with_routified_obj(app, router):
#     obj = mock.Mock()
#     obj.__growler_router = mock.NonCallableMock()
#     app.use(obj)
#     router.add_router.assert_called_with(None, obj.__growler_router)


# def xtest_use_with_routified_class(app, router):
#     sub_router = mock.Mock()
#     obj = mock.MagicMock()
#     obj.__growler_router.return_value = sub_router
#     obj.__growler_router.__class__ = types.MethodType
#     app.use(obj)
#     router.add_router.assert_called_with(None, sub_router)
#     obj.__growler_router.assert_called()


def test_enable(app):
    app.enable('option')
    assert app.enabled('option')


def test_enabled(app):
    app.enable('option')
    assert app.enabled('opti') is None


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


@pytest.mark.asyncio
async def test_default_error_handler_gets_called(app, req, res):

    ex = Exception("boom")
    m_handler = app.default_error_handler = mock.MagicMock()
    @app.use # (mock.MagicMock(side_effect=Exception("boom")))
    def bad_mw(req, res):
        raise ex

    app.print_middleware_tree()
    await app.handle_client_request(req, res)
    assert m_handler.called
    m_handler.assert_called_with(req, res, ex)


def test_default_error_handler_sends_res(app, req, res):
    ex = Exception("boom")
    app.default_error_handler(req, res, ex)
    assert res.send_html.called


@pytest.mark.asyncio
async def test_handle_client_request_coro(app, req, res):
    m = mock.Mock()
    coro = types.coroutine(lambda req, res: m())
    app.use(coro)
    await app.handle_client_request(req, res)
    assert m.called


@pytest.mark.asyncio
async def test_handle_client_request_exception(app, req, res, mock_route_generator):
    generator = mock.MagicMock()
    handler = mock.MagicMock()
    middleware = mock.Mock(return_value=generator)
    app.middleware = middleware

    async def handle_server_err(*args):
        handler(*args)

    app.handle_server_error = handle_server_err

    ex = Exception("boom")
    m1 = mock_route_generator()
    m1.side_effect = ex

    generator.__iter__.return_value = [m1]

    await app.handle_client_request(req, res)

    assert generator.throw.called
    assert len(handler.mock_calls) is 1
    handler.assert_called_with(req, res, generator, ex)


@pytest.mark.asyncio
async def test_handle_client_request_nosend(app, req, res, mock_route_generator):
    res.has_ended = False

    generator = mock.MagicMock()
    generator.__iter__.return_value = []
    middleware = mock.Mock(return_value=generator)
    app.middleware = middleware

    await app.handle_client_request(req, res)
    assert res.send_html.called


@pytest.mark.asyncio
@pytest.mark.parametrize('req_uri, middlewares, called', [
    ('/', [], True),
    # ('/aaa', [], False),
])
async def test_handle_client_request_get(app, req, res, middlewares, called, mock_route_generator):
    m1 = mock_route_generator()
    app.use(m1)
    await app.handle_client_request(req, res)
    assert m1.called is called


@pytest.mark.asyncio
async def test_middleware_stops_with_stop_iteration(app, req, res):
    async def do_something(req, res):
        return None

    def mock_function():
        # this coroutine required to let test pass - unknown why
        # return asyncio.coroutine(mock.create_autospec(do_something))
        return mock.create_autospec(do_something)

    m1 = mock_function()
    m2 = mock_function()

    m1.side_effect = GrowlerStopIteration

    app.use(m1)
    app.use(m2)

    await app.handle_client_request(req, res)

    assert not m2.called


@pytest.mark.asyncio
async def test_middleware_stops_with_res(app, req, res):
    res.has_ended = False

    def set_has_ended(Q, S):
        res.has_ended = True

    m1 = mock.MagicMock(spec=set_has_ended,
                        __name__='set_has_ended',
                        __qualname__='set_has_ended',
                        __annotations__={},
                        __code__=set_has_ended.__code__)
    m2 = mock.MagicMock(spec=set_has_ended,
                        __name__='set_has_ended',
                        __qualname__='set_has_ended',
                        __annotations__={},
                        __code__=set_has_ended.__code__,
                        side_effect=set_has_ended)
    m3 = mock.MagicMock(spec=set_has_ended,
                        __name__='set_has_ended',
                        __qualname__='set_has_ended',
                        __annotations__={},
                        __code__=set_has_ended.__code__)

    app.use(m1)
    app.use(m2)
    app.use(m3)

    await app.handle_client_request(req, res)

    assert m1.called
    assert m2.called
    assert not m3.called


@pytest.mark.asyncio
async def test_middleware_stops_with_growlerstopiter(app, req, res):
    res.has_ended = False

    m0 = mock.MagicMock()
    m1 = mock.MagicMock()

    @app.use
    def passes(req, res):
        m0(req, res)

    @app.use
    def stop_iter(req, res):
        raise GrowlerStopIteration

    @app.use
    def passes_again(req, res):
        m1(req, res)

    await app.handle_client_request(req, res)

    m0.assert_called_with(req, res)
    m1.assert_not_called
    assert res.has_ended == False


@pytest.mark.asyncio
async def test_handle_server_error(app, req, res):
    m1 = mock.create_autospec(lambda rq, rs, er: None)
    m2 = mock.create_autospec(lambda rq, rs, er: None)
    def set_has_ended(Q, S, E):
        res.has_ended = True

    m1.side_effect = set_has_ended
    generator = mock.MagicMock()
    generator.__iter__.return_value = [m1, m2]
    err = mock.MagicMock()

    await app.handle_server_error(req, res, generator, err)
    assert m1.called
    assert not m2.called


@pytest.mark.asyncio
async def test_handle_server_error_awaitable(app, req, res):
    res.has_ended = False
    ex = Exception("Boom")
    m0 = mock.MagicMock()
    eh = mock.MagicMock()
    m1 = mock.MagicMock()

    def m_call(m):
        return lambda req, res: m(req, res)

    async def ehandle(req, res, err):
        eh(req, res, err)
        assert err is None

    async def oops(req, res):
        raise ex

    app.use(m_call(m0))
    app.use(ehandle)
    e = app.middleware.mw_list[-1]

    app.use(m_call(m1))
    app.use(oops)
    app.print_middleware_tree()
    await app.handle_client_request(req, res)

    m0.assert_called_with(req, res)
    m1.assert_called_with(req, res)
    eh.assert_called_with(req, res, ex)


@pytest.mark.asyncio
async def test_handle_server_error_sends_status_500(app, req, res):
    ex = Exception("Boom!")
    gen = mock.MagicMock()

    @app.use
    def raises_err(rq, rs):
        gen(rq, rs)
        raise ex

    await app.handle_client_request(req, res)
    gen.assert_called_once_with(req, res)
    args = res.send_html.call_args[0]
    assert args[1] == 500
    assert '500 -' in args[0]


@pytest.mark.asyncio
@pytest.mark.parametrize('count, passes', [
    (0, True),
    (Application.error_recursion_max_depth-1, True),
    (Application.error_recursion_max_depth, False),
    (Application.error_recursion_max_depth+2, False),
])
async def test_handle_server_error_max_depth(app, req, res, count, passes):
    generator = mock.MagicMock()
    generator.__iter__.return_value = []
    err = mock.MagicMock()

    if passes:
        await app.handle_server_error(req, res, generator, err, count)
    else:
        with pytest.raises(Exception):
            await app.handle_server_error(req, res, generator, err, count)


@pytest.mark.asyncio
async def test_handle_server_error_in_error(app, req, res):
    generator = mock.MagicMock()
    m1 = mock.create_autospec(lambda rq, rs, er: None)
    m2 = mock.create_autospec(lambda rq, rs, er: None)

    def reset_iteration(Q, S, E):
        generator.__iter__.return_value = []
        raise ex

    ex = Exception("boom")
    m1.side_effect = reset_iteration

    generator.__iter__.return_value = [m1, m2]
    err = mock.MagicMock()

    await app.handle_server_error(req, res, generator, err)

    assert m1.called
    assert not m2.called


@pytest.mark.asyncio
async def test_response_not_sent(app, req, res):
    req.method = 0b000001
    req.path = '/'
    res.has_ended = False

    def send_req(rq, rs):
        rs.has_ended = True

    foo = mock.Mock(_is_coroutine=False, side_effect=send_req)
    app.get("/foo", foo)
    bar = mock.Mock(_is_coroutine=False, side_effect=send_req)
    app.get("/bar", bar)
    app.handle_response_not_sent = mock.Mock()
    await app.handle_client_request(req, res)
    foo.assert_not_called
    bar.assert_not_called
    app.handle_response_not_sent.assert_called_with(req, res)
