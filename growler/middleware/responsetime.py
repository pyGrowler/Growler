#
# growler/middleware/responsetime.py
#

import time


class ResponseTime(object):
    """
    Middleware which saves the time when initially called, and sets an
    'on_headers' event to get the time difference which can be logged or sent
    to the client.
    """

    def __init__(self, digits=3, header="X-Response-Time", suffix=True):
        self.digits = digits
        self.header = header
        self.suffix = suffix

    def __call__(self, req, res, next):
        start_time = time.time()

        def on_header_send():
            time.sleep(0.2)
            print("[on_header_send]")
            # if header already exists, do NOT clobber it
            if self.header in res.headers:
                return
            dt = round(1000 * (time.time() - start_time), self.digits)
            val = "{}{}".format(dt, "ms") if self.suffix else dt
            res.set(self.header, val)

        res.on_headers(on_header_send)
