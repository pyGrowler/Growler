#
# tests/test_event_emitter
#

import pytest
import asyncio

from unittest import mock
from growler.utils.event_manager import event_emitter, Events


@pytest.fixture
def loop(event_loop):
    return event_loop


@pytest.fixture
def mock_func(loop):
    return mock.create_autospec(lambda: None)


@event_emitter
class EE:

    def foo(self):
        return 0


@event_emitter(events=['good'])
class EEE:
    pass


def test_method_addition():
    e = EE()
    assert hasattr(e, 'on')
    assert hasattr(e, 'emit')


def test_on_method():
    e = EE()
    assert e.on('x', lambda: 'y') is e


def test_on_bad_callback():
    e = EE()
    with pytest.raises(ValueError):
        e.on('x', 'y')


def test_on_bad_name():
    e = EEE()
    with pytest.raises(KeyError):
        e.on('bad', mock.Mock())


def test_on_good_name(loop, mock_func):
    e = EEE()
    e.on('good', mock_func)
    emit_coro = e.emit('good')
    loop.run_until_complete(emit_coro)
    assert mock_func.called


# @pytest.mark.asyncio
# async def test_coro_callback(): #loop, mock_func):
#     e = EEE()
#     async def foo():
#         return 10
#     e.on('good', foo)
#     emit_coro = e.emit('good')
#     await emit_coro
#     assert mock_func.called


def test_events_constructor_empty():
    e = Events()
    e.on('anything', lambda: print())


def test_events_constructor_nonempty():
    e = Events('foo')
    with pytest.raises(KeyError):
        e.on('anything', lambda: print())

def test_events_on_typecheck():
    e = Events('foo')
    with pytest.raises(ValueError):
        e.on('anything', 10)

@pytest.mark.asyncio
def test_events_on_decorator():
    e = Events('foo')
    m = mock.MagicMock()

    @e.on("foo")
    def doit():
        m()
    yield from e.emit("foo")
    assert m.called

@pytest.mark.asyncio
def test_events_on():
    e = Events('foo')
    m = mock.MagicMock()
    e.on('foo', m)
    yield from e.emit('foo')
    assert m.called

@pytest.mark.asyncio
def test_events_on_async():
    e = Events('foo')
    m = mock.MagicMock()

    @asyncio.coroutine
    def foo():
        m()

    e.on('foo', foo())
    yield from e.emit('foo')
    assert m.called
