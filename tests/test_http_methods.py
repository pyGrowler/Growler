#
# tests/test_http_method.py
#


import growler
import pytest
from growler.http import HTTPMethod


def test_all():
    NOT_ALL = set(HTTPMethod) - {HTTPMethod.ALL}
    for i in NOT_ALL:
        assert HTTPMethod.ALL & i
