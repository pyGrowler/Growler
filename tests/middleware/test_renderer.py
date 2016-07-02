#
# tests/middleware/test_renderer.py
#

import re
import sys
import types
import pytest
import asyncio
import growler

from pathlib import Path
from unittest import mock
from growler.middleware.renderer import Renderer, RenderEngine, StringRenderer


@pytest.fixture
def mock_renderer():
    r = mock.MagicMock(spec=Renderer(mock.Mock()))
    return r


@pytest.fixture
def res(mock_renderer):
    m = mock.Mock()
    m.render = mock_renderer
    return m


@pytest.fixture
def req():
    return mock.Mock()


@pytest.fixture
# def renderer(mock_response):
def renderer():
    m = mock.MagicMock()
    return Renderer(m)


@pytest.fixture
def base_renderer(tmpdir):
    return RenderEngine(str(tmpdir))


@pytest.fixture
def string_renderer(tmpdir):
    return StringRenderer(str(tmpdir))


# @pytest.mark.parametrize("tmpdir", r"/a/random/path")
def test_string_renderer_fixture(string_renderer, tmpdir):
    assert isinstance(string_renderer, StringRenderer)
    assert str(string_renderer.path) == str(tmpdir)


def test_string_renderer_fixture(string_renderer, tmpdir):
    assert isinstance(string_renderer, StringRenderer)
    assert str(string_renderer.path) == str(tmpdir)


def test_render_engine_adds_render_method(base_renderer, req):
    res = mock.create_autospec(1)
    assert not hasattr(res, 'render')
    # renderer = RenderEngine()
    base_renderer(req, res)
    assert hasattr(res, 'render')
    assert hasattr(res, 'locals')


def test_renderer_requires_real_path(tmpdir):
    with pytest.raises(FileNotFoundError):
        RenderEngine(str(tmpdir / 'does-not-exist'))


def test_renderer_constructor_requires_directory(tmpdir):
    not_a_dir = tmpdir / 'simple_file'
    not_a_dir.write('')

    with pytest.raises(NotADirectoryError):
        RenderEngine(str(not_a_dir))


def test_missing_file(string_renderer, tmpdir, renderer, req):

    res = mock.create_autospec(1)
    string_renderer(req, res)

    with pytest.raises(ValueError):
        res.render('does-not-exist')


def test_find_template_filename(string_renderer, tmpdir):
    foo_file = tmpdir / 'foo.html.tmpl'
    foo_file.write('')
    filename = string_renderer.find_template_filename('foo')
    assert filename == Path(str(foo_file))


def test_find_template_no_extensions(base_renderer, tmpdir):
    foo_file = tmpdir / 'foo.txt'
    foo_file.write('')
    filename = base_renderer.find_template_filename('foo')
    assert filename is None



def test_find_template_with_extensions(base_renderer, tmpdir):
    foo_file = tmpdir / 'foo.txt'
    foo_file.write('')
    base_renderer.default_file_extensions = ['.txt']
    filename = base_renderer.find_template_filename('foo')
    assert filename == Path(str(foo_file))


def test_find_missing_template_filename(string_renderer):
    result = string_renderer.find_template_filename('foo')
    assert result is None


def test_render_source(string_renderer, tmpdir):
    data = r"spam-{spam}"

    foo_file = tmpdir / 'foo.txt'
    foo_file.write(data)

    result = string_renderer.render_source('foo.txt', {'spam': 'a-lot'})

    assert result == "spam-a-lot"
