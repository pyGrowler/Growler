#
# tests/middleware/test_session.py
#

import uuid
import pytest
import growler
from unittest import mock
from growler.middleware import session


@pytest.fixture
def mock_backend():
    try:
        from unittest.mock import AsyncMock
    except ImportError:
        AsyncMock = None

    if not AsyncMock:
        mock = pytest.importorskip('mock')
        AsyncMock = mock.AsyncMock

    return AsyncMock()


@pytest.fixture
def sess(mock_backend):
    return session.Session(mock_backend)


def test_sess_fixture(sess):
    assert isinstance(sess, session.Session)


def test_getters_and_setters(sess):
    data = 'foo'
    sess['data'] = data

    assert sess['data'] is data
    assert sess.get('data') is data
    assert sess.get('notFound') is None
    assert len(sess) == 1

    for i in sess:
        assert i == 'data'

    del sess['data']
    assert 'data' not in sess
    assert len(sess) == 0


@pytest.mark.asyncio
async def test_session_save(sess, mock_backend):
    await sess.save()
    mock_backend.save.assert_called_with(sess)


@pytest.fixture
def storage():
    return session.DefaultSessionStorage()


def test_storage_fixture(storage):
    assert isinstance(storage, session.DefaultSessionStorage)


def test_defaultstorage_call_nocookie(storage):
    name = 'Fooo'
    storage.session_id_name = name
    req, res = mock.MagicMock(), mock.MagicMock()
    req.cookies = {}
    storage(req, res)
    assert isinstance(req.session, session.Session)
    assert isinstance(req.cookies[name], uuid.UUID)


def test_defaultstorage_call(storage):
    req, res = mock.MagicMock(), mock.MagicMock()
    storage(req, res)
    assert isinstance(req.session, session.Session)


def test_defaultstorage_save(storage):
    m = mock.MagicMock()
    storage.save(m)
    assert storage._sessions[m.id] is m._data
