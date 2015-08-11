#
# tests/test_http_method.py
#


import growler
import pytest
import growler.http.methods


def test_get_method():
    method = growler.http.HTTPMethod.GET
    assert growler.http.methods.string_to_method["GET"] is method


def test_post_method():
    method = growler.http.HTTPMethod.POST
    assert growler.http.methods.string_to_method["POST"] is method


def test_put_method():
    method = growler.http.HTTPMethod.PUT
    assert growler.http.methods.string_to_method["PUT"] is method


def test_delete_method():
    method = growler.http.HTTPMethod.DELETE
    assert growler.http.methods.string_to_method["DELETE"] is method
