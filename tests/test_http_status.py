#
# tests/test_http_status.py
#

import pytest
from growler.http.status import Status


@pytest.mark.parametrize("code, phrase", [
    (100, "Continue"),
    (200, 'OK'),
    (403, 'Forbidden'),
    (404, 'Not Found'),
    (500, "Internal Server Error"),
])
def test_phrase(code, phrase):
    assert Status.phrase_dict[code] == phrase
    assert Status.Phrase(code) == phrase
