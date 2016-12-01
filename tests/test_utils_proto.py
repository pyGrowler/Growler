#
# tests/test_utils_proto.py
#

import pytest
from unittest.mock import MagicMock
from growler.utils.proto import PrototypeMeta, PrototypeObject


def test_metaclass():
    a = PrototypeObject()
    assert isinstance(type(a), PrototypeMeta)


def test_inheritence():
    a = PrototypeObject()
    a.x = 123
    b = PrototypeObject()
    b.__proto__ = a

    assert b.x == 123

    b.x = -8

    assert a.x == 123
    assert b.x == -8

    assert not hasattr(b, 'y')

    a.y = 'y'

    assert b.y is a.y


@pytest.fixture
def a():
    a = PrototypeObject()
    a.x = 1e3
    return a


@pytest.fixture
def b(a):
    b = PrototypeObject.create(a)
    b.y = 5000
    return b


def test_create_fixtues(a, b):
    assert b.x is a.x
    assert hasattr(b, 'y')
    assert hasattr(b, 'x')
    assert hasattr(a, 'x')
    assert not hasattr(a, 'y')


def test_has_own_property(a, b):
    assert b.has_own_property('y')
    assert not b.has_own_property('x')


def test_del_property(a, b):
    assert hasattr(b, 'y')
    del b.y
    del b.x

    assert not hasattr(b, 'y')
    assert b.x is a.x


def test_setter_property(a, b):
    b.x += 1
    assert b.x == a.x + 1


def test_no_attribute(a, b):
    with pytest.raises(AttributeError):
        del b.boom


def test_del_no_attribute(a, b):
    with pytest.raises(AttributeError):
        del b.no_attr


def test_del_proto(a, b):
    with pytest.raises(RuntimeError):
        del b.__proto__

    with pytest.raises(RuntimeError):
        del b.__methods__


def test_bind_function(a, b):

    # @a.method.f
    def f(self, x):
        x(self)

    # a.bind(f, 'f')
    a.bind(f)

    ma = MagicMock()
    a.f(ma)
    ma.assert_called_with(a)

    mb = MagicMock()
    b.f(mb)
    mb.assert_called_with(b)
