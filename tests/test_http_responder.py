#
#
#


import asyncio
import pytest

import growler
from growler.http.responder import GrowlerHTTPResponder
from growler.http.error import (
    HTTPErrorBadRequest,
    HTTPErrorNotImplemented,
    HTTPErrorVersionNotSupported,
)


class mock_protocol():

    def __init__(self, data=[]):
        self.loop = asyncio.get_event_loop()
        self.http_application = None


class mock_parser():

    def __init__(self, parent):
        self.parent = parent
        self.i = 0
        self.data = []

    def consume(self, data, stuff=0):
        if stuff == 0:
            self.parent.set_request_line(data, 2, 3)
        else:
            self.parent.set_headers(data.decode())


def test_responder_constructor():
    p = mock_protocol()
    r = GrowlerHTTPResponder(p)
    assert r.loop == p.loop


def notest_on_parsing_queue():
    loop = asyncio.get_event_loop()
    r = GrowlerHTTPResponder(mock_protocol(), mock_parser)
    r.parsing_task.cancel()

    @asyncio.coroutine
    def _():
        output = yield from r.parsing_queue.get()
        assert output == 'spam'

    r.parsing_queue.put_nowait('spam')
    loop.run_until_complete(_())


if __name__ == '__main__':
    test_on_parsing_queue_1()
