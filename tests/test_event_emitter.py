#
# tests/test_event_emitter
#

from growler.utils.event_manager import event_emitter
from unittest import mock
import pytest
import asyncio


@pytest.fixture
def loop():
    return asyncio.get_event_loop()


@pytest.fixture
def mock_func():
    return mock.MagicMock(asyncio.get_event_loop)


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
