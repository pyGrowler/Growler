#
# tests/middleware/test_auth.py
#

import growler
import pytest
from unittest import mock

from mock_classes import (                                               # noqa
    mock_protocol,
    request_uri,
)


@pytest.fixture
def auth():
    return growler.middleware.auth.Auth()


def test_constructor(auth):
    assert isinstance(auth, growler.middleware.auth.Auth)


def test_docstring(auth):
    doc = auth.__doc__
    assert isinstance(doc, str)


def test_call(auth):
    do_auth = auth()
    assert callable(do_auth)
    with pytest.raises(NotImplementedError):
        do_auth(mock.Mock(), mock.Mock())

def test_do_authentication(auth):
    with pytest.raises(NotImplementedError):
        auth.do_authentication(mock.Mock(), mock.Mock())
