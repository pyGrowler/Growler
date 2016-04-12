#
# growler/middleware/responsetime.py
#
"""
Provides middleware which adds a header indicating how long the request took to
process
"""

import time


class ResponseTime:
    """
    Middleware which saves the time when initially called, and sets an
    'on_headers' event to get the time difference which can be logged or sent
    to the client.
    """

    UNIT_TO_FACTOR_MAP = {
        's': 1,
        'ms': 1000,
        'us': 1000000,
    }

    def __init__(self,
                 digits=3,
                 units='ms',
                 header="X-Response-Time",
                 suffix=True,
                 clobber_header=False):

        factor = self.UNIT_TO_FACTOR_MAP[units]

        def format_timediff(td):
            return str(round(factor * td, digits))

        self.format = format_timediff
        self.units = units
        self.header = header
        self.suffix = suffix
        self.clobber_header = clobber_header

    def __call__(self, req, res):
        start_time = time.monotonic()

        def on_header_send():
            # if header already exists, do NOT clobber it
            if not self.clobber_header and self.header in res.headers:
                return

            dt = self.format(time.monotonic() - start_time)
            val = "{}{}".format(dt, self.units) if self.suffix else dt
            res.set(self.header, val)

        res.on_headers(on_header_send)
