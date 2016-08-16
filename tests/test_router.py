#
# tests/test_router.py
#

import growler
from growler.router import (
    Router,
    HTTPMethod,
    get_routing_attributes,
)
from unittest import mock
import pytest
import re
import types


GET = HTTPMethod.GET
POST = HTTPMethod.POST
PUT = HTTPMethod.PUT
DELETE = HTTPMethod.DELETE


@pytest.fixture
def req_path():
    return "/"


@pytest.fixture
def req_method():
    return GET


@pytest.fixture
def mock_req(req_path, req_method):
    return mock.MagicMock(spec=growler.http.request.HTTPRequest,
                          path=req_path,
                          method=req_method)


@pytest.fixture
def router():
    router = growler.router.Router()
    return router


@pytest.fixture
def mock_router():
    return mock.Mock(spec=growler.router.Router,
                     __class__=growler.router.Router,
                     return_value=[])


@pytest.mark.parametrize("test_route, req_path, req_method, should_call", [
    ((GET, "/", mock.Mock()), "/", GET, True),
    ((GET, "/", mock.Mock()), "/x", GET, False),
    ((GET, "/x", mock.Mock()), "/", GET, False),
    ((POST, "/", mock.Mock()), "/x", GET, False),
    ((POST, "/", mock.Mock()), "/", GET, False),
    ((POST, "/", mock.Mock()), "/x", POST, False),
    ((POST, "/x", mock.Mock()), "/x", POST, True),
])
def test_add_route(router, mock_req, test_route, should_call):
    func = test_route[2]
    router.add_route(*test_route)
    m = [x for x in router.match_routes(mock_req)]
    if not should_call:
        assert len(m) is 0
    else:
        assert len(m) is 1
        assert m[0] is func


@pytest.mark.parametrize("middleware, req_path, req_method, should_call", [
    ((mock.Mock(), None), "/", GET, True),
    ((mock.Mock(), "/a"), "/a", GET, True),
    ((mock.Mock(), "/x"), "/", GET, False),
    ((mock.Mock(), '/x'), "/x", GET, True),
    ((mock.Mock(), '/x'), "/x", POST, True),
])
def test_use(router, mock_req, middleware, should_call):
    func = middleware[0]
    router.use(*middleware)
    m = list(router.match_routes(mock_req))
    if should_call:
        assert len(m) is 1
        assert m[0] is func
    else:
        assert len(m) is 0


# @pytest.mark.parametrize("mount, req_path, matches", [
#     ("/", "/aa", True),
#     ("/x", "/x/aa", True),
#     ("/x/", "/x/aa", True),
#     ("/x", "/aa", False),
#     ("/y/", "/x/y", False),
# ])
# def test_add_router(router, mock_router, mock_req, mount, matches):
#     subrouter_count = len(router.subrouters)
#     router.add_router(mount, mock_router)
#     assert len(router.subrouters) == subrouter_count + 1
#     for route in router.match_routes(mock_req):
#         pass
#     if matches:
#         assert mock_router.called
#     else:
#         assert not mock_router.called


@pytest.mark.parametrize("method_func, method_key", [
    (Router.all, HTTPMethod.ALL),
    (Router.get, HTTPMethod.GET),
    (Router.post, HTTPMethod.POST),
    (Router.delete, HTTPMethod.DELETE),
])
def test_auto_methods(router, method_func, method_key):
    m = mock.Mock()
    method_func(router, '/foo', m)

    assert router.last().func is m
    assert router.last().mask is method_key

    @method_func(router, '/foo')
    def foo(req, res):
        pass

    assert isinstance(foo, types.FunctionType)
    assert router.last().func is foo
    assert router.last().mask is method_key


@pytest.mark.parametrize("path, req_path, matches", [
    ("/", "/", True),
    ("/name/:name", "/name/foo", True),
    ("/", "/x", False),
    ("/y", "/x", False),
])
def test_sinatra_path_matches(path, req_path, matches):
    r = Router.sinatra_path_to_regex(path)
    assert (r.fullmatch(req_path) is not None) == matches


@pytest.mark.parametrize("path, req_path, match_dict", [
    ("/", "/", {}),
    ("/:x", "/yyy", {"x": "yyy"}),
    ("/user/:user_id", "/user/500", {"user_id": "500"}),
    ("/:x/:y", "/10/345", {"x": "10", "y": "345"}),
    ("/:x/via/:y", "/010/via/101", {"x": "010", "y": "101"}),
])
def test_sinatra_path_groupdict(path, req_path, match_dict):
    r = Router.sinatra_path_to_regex(path)
    m = r.match(req_path)
    assert m.groupdict() == match_dict


@pytest.mark.parametrize("mounts, req_path, match_dict", [
    (("/", "/"), "/", {}),
    (("/a/b", "/:x"), "/a/b/c", {'x': "c"}),
])
def test_subrouter_groupdict(router, mock_req, mounts, req_path, match_dict):
    subrouter = Router()
    endpoint = mock.Mock()
    subrouter.add_route(GET, mounts[1], endpoint)
    router.add_router(mounts[0], subrouter)
    m = [x for x in router.match_routes(mock_req)]
    if m:
        assert m[0] is endpoint


class Foo:

    def __init__(self, x):
        self.x = x

    def get_something(self, req, res):
        """/"""
        return self.x


def test_sinatra_passes_regex():
    import re
    s = re.compile('/name/:name')
    r = Router.sinatra_path_to_regex(s)
    assert r.match("/not/right") is None


def test_routerify():
    from growler.router import routerify

    foo = Foo('1')
    routerify(foo)
    assert hasattr(foo, '__growler_router')
    first_route = foo.__growler_router.routes[0]
    assert first_route[0] == GET
    assert first_route[1] == re.compile('\\/')
    assert first_route[2](None, None) is foo.get_something(None, None)


def test_mock_routerclass():
    cls = growler.router.routerclass(mock.MagicMock())
    assert isinstance(cls.__growler_router, types.FunctionType)
    # obj = cls()
    # print(dir(obj))
    # assert isinstance(obj.__growler_router, types.FunctionType)
    # apply cls.__growler_router
    # obj.__growler_router()


def test_routerclass():
    from growler.router import routerclass

    @routerclass
    class SubFoo(Foo):
        def get_what(self, req, res):
            pass

    sf = SubFoo('X')
    assert isinstance(sf.__growler_router, types.MethodType)

    # We must CALL __growler_router to routerify with the instance itself
    sf.__growler_router()
    assert hasattr(sf, '__growler_router')
    first_route = sf.__growler_router.routes[0]
    assert first_route[0] == GET
    assert first_route[1] == re.compile('\\/')
    assert first_route[2](None, None) is sf.get_something(None, None)
    assert len(sf.__growler_router.routes) == 1

    foo = SubFoo('Y')
    foo.__growler_router()
    foo_route = foo.__growler_router.routes[0]
    assert first_route[2](None, None) is not foo_route[2](None, None)


def test_router_metaclass(router):
    from growler.router import RouterMeta

    class MyRouter(metaclass=RouterMeta):

        get_something = 153

        def get_foo(self, req, res):
            """/abc/efg"""
            pass

        def get_skip(self, req, res):
            """"""
            pass

        def get_bar(self, req, res):
            """/xyz/ijk"""
            pass

    assert callable(MyRouter._RouterMeta__growler_router)
    sub_router = MyRouter()
    new_router = sub_router._RouterMeta__growler_router()
    assert len(new_router) is 2
    assert new_router.first().func.__func__ is MyRouter.get_foo
    assert new_router.last().func.__func__ is MyRouter.get_bar


@pytest.mark.parametrize("attrs", [
    [('get_a', '/a'), ('get_b', '/b')]
])
def test_get_routing_attributes(attrs):
    m = mock.Mock()
    mounts = []
    for path, doc in attrs:
        getattr(m, path).__doc__ = doc
        mounts.append(doc.split()[0])
    rets = tuple(i[1] for i in get_routing_attributes(m))
    assert all(a == b for a, b in zip(rets, mounts))


@pytest.mark.parametrize("attrs", [
    [('get_a', '/a blah blah blah', '/a', 'blah blah blah'),
     ('get_b', '/b', '/b', ''),
    ],
])
def test_get_routing_attributes_modify_doc(attrs):
    m = mock.Mock()
    paths = []
    docs = []
    for name, doc, path, newdoc in attrs:
        getattr(m, name).__doc__ = doc
        paths.append(path)
        docs.append(newdoc)
    rets = tuple(get_routing_attributes(m, True))
    for a, b, c in zip(rets, paths, docs):
        assert a[1] == b
        assert a[2].__doc__ == c


def test_property_subrouter(router):
    subrouter = Router()
    router.add(0, '/', subrouter)
    subrouters = list(router.subrouters)
    assert len(subrouters) == 1
    assert subrouters[0].func is subrouter


def test_find_routable_attributes(router):
    class TestMe:
        def get_something():
            "/should/work"
            pass
        def get_nothing():
            pass
        get_something_else = 'not callable'

    keys = [
        'get_something', # should work
        'get_nothing', # should not work - no docstring
        'post_skip', # should not work - doesn't actually exist in object
        'get_something_else', # should not work - not callable
    ]

    obj = TestMe()
    for x, y in growler.router._find_routeable_attributes(obj, keys):
        assert y == 'GET'
        assert x == obj.get_something
