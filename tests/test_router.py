#
# tests/test_router.py
#

import growler
from growler.router import Router
from unittest import mock
import pytest


# @pytest.fixture
# def req_path():
#     return "??"


@pytest.fixture
def mock_req(req_path):
    return mock.MagicMock(spec=growler.http.request.HTTPRequest,
                          path=req_path,
                          method="GET")


@pytest.fixture
def router():
    router = growler.router.Router()
    return router


@pytest.fixture
def mock_router():
    router = mock.MagicMock(spec=growler.router.Router)
    return router


@pytest.mark.parametrize("mount, req_path, mount_at", [
    ("/", "/blahh", "/blahh"),
    ("/x", "/x/blahh", "/blahh"),
    ("/x/", "/x/blahh", "/blahh"),
    ("/x", "/y/A", None),
])
def test_add_router(router, mock_router, mock_req, mount, req_path, mount_at):
    router.add_router(mount, mock_router)
    assert len(router.subrouters) == 1
    for route in router.match_routes(mock_req):
        pass
    if mount_at is None:
        assert mock_router.match_routes.called is False
    else:
        mock_router.match_routes.assert_called_with(mock_req)


@pytest.mark.parametrize("method, mount_point, endpoint, req_path", [
    ("GET", "/", " ", "/"),
    ("GET", "/", None, "/x"),
    ("POST", "/", None, "/x"),
])
def test_add_route(router, mock_req, method, mount_point, endpoint, req_path):
    router.add_route(method, mount_point, endpoint)
    m = [x for x in router.match_routes(mock_req)]
    if endpoint is None:
        assert len(m) is 0
    else:
        assert len(m) is 1
        assert m[0] is endpoint


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
    assert first_route[0] == 'GET'
    assert first_route[1] == '/'
    assert first_route[2](None, None) is foo.get_something(None, None)


def test_routerclass():
    from growler.router import routerclass
    from types import MethodType

    @routerclass
    class SubFoo(Foo):
        def get_what(self, req, res):
            pass

    sf = SubFoo('X')
    assert isinstance(sf.__growler_router, MethodType)

    # We must CALL __growler_router to routerify with the instance itself
    sf.__growler_router()
    assert hasattr(sf, '__growler_router')
    first_route = sf.__growler_router.routes[0]
    assert first_route[0] == 'GET'
    assert first_route[1] == '/'
    assert first_route[2](None, None) is sf.get_something(None, None)
    assert len(sf.__growler_router.routes) == 1

    foo = SubFoo('Y')
    foo.__growler_router()
    foo_route = foo.__growler_router.routes[0]
    assert first_route[2](None, None) is not foo_route[2](None, None)
