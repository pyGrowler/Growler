#
#
#


import asyncio
import pytest

import growler
from growler.http.responder import GrowlerHTTPResponder
from growler.http.Error import (
    HTTPErrorBadRequest,
    HTTPErrorNotImplemented,
    HTTPErrorVersionNotSupported,
)

class mock_protocol():

    def __init__(self, data=[]):
        self.loop = asyncio.get_event_loop()
        self.growler_app = None

class mock_parser():

    def __init__(self, queue):
        self.queue = queue
        self.i = 0
        self.data = []

    def consume(self, data):
        if self.data:
            self.queue.put_nowait(self.data.pop(0))
        else:
            self.queue.put_nowait(data.decode())

def test_responder_constructor():
    p = mock_protocol()
    r = GrowlerHTTPResponder(p)
    assert r.loop == p.loop

def test_on_parsing_queue():
    loop = asyncio.get_event_loop()
    r = GrowlerHTTPResponder(mock_protocol(), mock_parser)
    r.parsing_task.cancel()

    @asyncio.coroutine
    def _():
        output = yield from r.parsing_queue.get()
        assert output == 'spam'

    r.parsing_queue.put_nowait('spam')
    loop.run_until_complete(_())

def test_on_parsing_queue_1():

    loop = asyncio.get_event_loop()
    r = GrowlerHTTPResponder(mock_protocol(), mock_parser)
    r.on_data(b"GET")
    r.on_data(b"SPAM\n")
    loop.run_until_complete(r.parsing_task)

    assert r.parsed_request == 'GET'


if __name__ == '__main__':
    test_on_parsing_queue_1()
