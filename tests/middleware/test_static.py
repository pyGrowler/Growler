#
# tests/middleware/test_static.py
#

import pytest
import growler
import pathlib
from unittest import mock
from growler.middleware.static import Static


@pytest.fixture
def static(tmpdir):
    return Static(str(tmpdir))


def test_static_fixture(static, tmpdir):
    assert isinstance(static, Static)


def test_construct_with_list(tmpdir):
    s = Static(['/'] + str(tmpdir).split('/'))
    assert str(s.path) == str(tmpdir)


def test_error_on_missing_dir():
    with pytest.raises(Exception):
        Static("/does/not/exist")


def test_call(static, tmpdir):
    req, res = mock.MagicMock(), mock.MagicMock()

    file_contents = b'This is some text in teh file'

    f = tmpdir.mkdir('foo').mkdir('bar') / 'file.txt'
    f.write(file_contents)

    req.path = 'foo/bar/file.txt'

    # req.path
    static(req, res)

    res.set_type.assert_called_with('text/plain')
    res.send_file.assert_called_with(pathlib.Path(str(f)))


def test_call_invalid_path(static):
    req, res = mock.Mock(), mock.Mock()

    req.path = 'foo/../bar'
    static(req, res)

    assert not res.set_type.called
