#
# tests/test_router.py
#

from growler.router import Router


def test_sinatra_path():
    s = '/something'
    r = Router.sinatra_path_to_regex(s)
    assert r.match("/else") is None

    m = r.match(s)
    assert m is not None
    assert m.groupdict() == {}


def test_sinatra_key():
    s = '/name/:name'
    r = Router.sinatra_path_to_regex(s)
    assert r.match("/not/right") is None

    matches = r.match("/name/growler")
    assert matches.group('name') == 'growler'

    gd = matches.groupdict()
    assert gd['name'] == 'growler'


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


if __name__ == '__main__':
    test_sinatra_path()
