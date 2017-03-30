#
# tests/test_growler_ext.py
#

import sys
import pytest
from unittest import mock


def test_load_module():
    mod = mock.Mock()
    m = mock.Mock()
    m.name = 'foo'
    mi = mock.Mock(return_value=(m, ))
    mclass = mock.Mock()
    m.load.return_value = mclass
    mod.iter_entry_points = mi
    pkg_resources = sys.modules.get('pkg_resources')
    sys.modules['pkg_resources'] = mod
    import growler.ext as ext

    assert m.load.called
    assert getattr(ext, m.name) is mclass

    # reset pkg_resources module
    if pkg_resources is None:
        del sys.modules['pkg_resources']
    else:
        sys.modules['pkg_resources'] = pkg_resources
