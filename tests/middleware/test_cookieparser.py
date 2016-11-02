#
# tests/middleware/test_cookieparser.py
#

import pytest
from unittest import mock
from http.cookies import SimpleCookie
from growler.middleware.cookieparser import CookieParser


@pytest.fixture
def cp():
    return CookieParser()


@pytest.fixture
def req():
    m = mock.MagicMock()
    m.headers = {}
    del m.cookies
    return m


@pytest.fixture
def res():
    m = mock.MagicMock()
    del m.cookies
    m.headers = {}
    m.EOL = '\n'
    return m


def test_cp_fixture(cp):
    assert isinstance(cp, CookieParser)


def test_cp_does_not_clobber_cookies(cp, req, res):
    m = req.cookies = mock.MagicMock()
    cp(req, res)
    assert req.cookies is m


def test_cp_call(cp, req, res):
    cp(req, res)
    assert isinstance(req.cookies, SimpleCookie)
    assert isinstance(res.cookies, SimpleCookie)

    # set a cookie
    res.cookies['foo'] = 'bar'

    header = res.headers['Set-Cookie']()
    assert header == ' foo=bar'
