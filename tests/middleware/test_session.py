#
# tests/middleware/test_session.py
#

import pytest
import growler
from unittest import mock
from growler.middleware import session


@pytest.fixture
def backend():
    return mock.MagicMock()


@pytest.fixture
def sess(backend):
    return session.Session(backend)


def test_sess_fixture(sess):
    assert isinstance(sess, session.Session)

def test_sessi(sess):
    assert isinstance(sess, session.Session)
