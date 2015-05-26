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

if __name__ == '__main__':
    test_sinatra_path()
