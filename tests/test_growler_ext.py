#
# tests/test_growler_ext.py
#

import sys
import pytest
from unittest import mock
import growler.mw


@pytest.fixture
def mock_importer():
    import growler.ext
    return mock.create_autospec(growler.ext)


def test_module():
    import growler.ext
    assert growler.ext.__name__ == 'GrowlerExtensionImporter'


def test_load_module():
    mod = mock.Mock()
    sys.modules['growler_ext.xxxx'] = mod
    from growler.ext import xxxx
    assert xxxx is mod


def test_load_missing_module():
    with pytest.raises(ImportError):
        from growler.ext import yyy


def test_load_module_cached():
    import growler.ext
    growler.ext.__mods__ = mock.MagicMock()
    mod = growler.ext.mod_is_cached
    growler.ext.__mods__.__getitem__.assert_called_with("mod_is_cached")
