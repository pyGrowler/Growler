#
# growler/http/responder.py
#
"""
The Growler class responsible for responding to HTTP requests.
"""

import asyncio


class HTTPResponder():

    def __init__(self, protocol):
        """
        Construct an HTTPResponder. This should only be called from a growler
        protocol instance.
        """
        print("[HTTPResponder::HTTPResponder]")
        self.proto = protocol
        self.data_queue = protocol.data_queue
        self.proto.loop.create_task(self.data_loop())
        self.proto
        # self.proto.loop.call_soon(self.data_loop())

    def on_data(self, data):
        print("HTTP RECEIVED DATA")
        print(" ", data)
        self.proto.transport.write(b"Recieved. OK")
        # print ("Data Loop returned: ", data)

    @asyncio.coroutine
    def data_loop(self):
        count = 0
        while True:
            data = yield from self.data_queue.get()
            self.on_data(data)
            if data is None:
                break
            count += 1
