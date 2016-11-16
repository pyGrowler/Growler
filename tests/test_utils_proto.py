#
# tests/test_utils_proto.py
#

import pytest
from growler.utils.proto import PrototypeMeta, PrototypeObject


def test_metaclass():
    a = PrototypeObject()
    assert isinstance(type(a), PrototypeMeta)
