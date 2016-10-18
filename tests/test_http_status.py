#
# tests/test_http_status.py
#

import pytest
from growler.http import HttpStatus
import growler.http.errors as errors


@pytest.mark.parametrize("code, phrase", [
    (100, "Continue"),
    (200, 'OK'),
    (403, 'Forbidden'),
    (404, 'Not Found'),
    (500, "Internal Server Error"),
])
def test_phrase(code, phrase):
    assert HttpStatus(code).phrase == phrase
    # assert Status.phrase_dict[code] == phrase
    # assert Status.Phrase(code) == phrase


def test_error():
    with pytest.raises(errors.HTTPError):
        raise errors.HTTPErrorRequestedRangeNotSatisfiable()


def test_error_get_from_code():
    with pytest.raises(errors.HTTPErrorNotFound):
        raise errors.HTTPError.get_from_code(404)


@pytest.mark.parametrize("key, expected", [
    (404, errors.HTTPErrorNotFound),
    ('Forbidden', errors.HTTPErrorForbidden),
])
def test_error_getitem(key, expected):
    with pytest.raises(expected):
        raise errors.HTTPError[key]


@pytest.mark.parametrize("key", [
    5000,
    'Ferbiddon',
])
def test_error_get_invalid_item(key):
    with pytest.raises(errors.HTTPErrorInvalidHttpError):
        raise errors.HTTPError[key]


def test_error_message():
    not_found = errors.HTTPError[404]()
    assert not_found.msg == 'Not Found'
