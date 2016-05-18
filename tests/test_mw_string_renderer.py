#
# test_mw_string_renderer
#
# growler/middleware/renderer.py          58     37    36%   40-41, 60-69, 76-86, 92, 110, 122-126, 138, 151, 167-170, 173-174, 177-179
#

import sys
import pytest
from pathlib import Path
from unittest import mock
from growler.middleware.renderer import StringRenderer
from growler.http.response import HTTPResponse


@pytest.fixture
def res():
    return mock.create_autospec(HTTPResponse)


@pytest.fixture
def ren(res):
    return StringRenderer()

@pytest.fixture
def viewdir(tmpdir):
    return Path(str(tmpdir))

@pytest.fixture
def sr(viewdir):
    return StringRenderer(viewdir)


def test_string_renderer_fixture(sr):
    assert isinstance(sr, StringRenderer)


def test_render_file(sr, viewdir):
    txt = """Hello World"""
    view = viewdir.joinpath("hello.html")
    view.touch()

    if sys.version_info < (3, 5):  # python3.4 compat
        with open(str(view), 'w') as file:
            file.write(txt)
    else:
        view.write_text(txt)

    res = sr.render_source("hello.html")
    assert res == txt
