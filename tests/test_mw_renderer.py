#
# test_mw_string_renderer
#

import pytest
from unittest import mock
from growler.http.request import HTTPRequest
from growler.http.response import HTTPResponse
from growler.middleware.renderer import Renderer, RenderEngine


@pytest.fixture
def res():
    return mock.MagicMock(spec=HTTPResponse, locals={})
    return mock.create_autospec(HTTPResponse)


@pytest.fixture
def req():
    return mock.create_autospec(HTTPRequest)


@pytest.fixture
def mock_engine():
    # mock.Mock(spec="")
    return mock.create_autospec(RenderEngine)
    # return mock.MagicMock(spec=RenderEngine)


@pytest.fixture
def renderer(res, mock_engine):
    r = Renderer(res)
    r.add_engine(mock_engine)
    return r


def test_renderer_fixture(renderer):
    assert isinstance(renderer, Renderer)


def test_req_call(renderer, req, res):
    path = mock.Mock(spec="")
    obj = mock.MagicMock()
    renderer(path, obj)
