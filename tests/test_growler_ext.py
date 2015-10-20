#
# tests/test_growler_ext.py
#

import sys
import pytest
from unittest import mock


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


def test_load_module_cached():
    import growler.ext
    mod = mock.Mock()
    growler.ext.__mods__ = mock.MagicMock()
    growler.ext.__mods__.__contains__.return_value = True
    growler.ext.mod_is_cached
    assert growler.ext.__mods__.__getitem__.called
    growler.ext.__mods__.__contains__.assert_called_with("mod_is_cached")
