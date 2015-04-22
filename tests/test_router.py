#
# tests/test_router.py
#

from growler.router import Router

def test_sinatra_path():
    s = '/something'
    r = Router.sinatra_path_to_regex(s)
    q = r.match(s)
    print(q)
    assert q.groupdict() == {}
    
if __name__ == '__main__':
    test_sinatra_path()