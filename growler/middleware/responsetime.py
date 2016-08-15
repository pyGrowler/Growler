#
# growler/middleware/responsetime.py
#
"""
Provides middleware which adds a header indicating how long the request took to
process
"""

import time
import logging

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
                 log=None,
                 units='ms',
                 header="X-Response-Time",
                 suffix=True,
                 clobber_header=False):
        """
        Construct ResponseTime middleware.

        Parameters:
            digits (int): precision
            log (Logger or None): Writes the time difference to the log
            units (str): Time units (default: milliseconds 'ms')
            header (str): Name of header to send response time as
            suffix (bool): Whether to format with
        """
        self.units = units
        self.header_name = header
        self.digits = digits
        self.log = log
        self.suffix = suffix
        self.clobber_header = clobber_header

    def __call__(self, req, res):
        start_time = time.monotonic()

        def on_header_send():
            # if header already exists, do NOT clobber it
            if not self.clobber_header and self.header_name in res.headers:
                return

            dt = self.format_timediff(time.monotonic() - start_time)
            val = "{}{}".format(dt, self.units) if self.suffix else dt
            res.set(self.header_name, val)

            if self.log:
                self.log.info("-- timer %s" % val)

        res.events.on('before_headers', on_header_send)

    def format_timediff(self, td):
        factor = self.UNIT_TO_FACTOR_MAP[self.units]
        return str(round(factor * td, self.digits))
