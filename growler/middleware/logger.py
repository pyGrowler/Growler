#
# growler/middleware/logger.py
#
# flake8: noqa
#

import logging
import asyncio


class Logger:

    # Not pep8 but much better!
    DEFAULT = '/033[30m'
    RED     = '/033[31m'
    GREEN   = '/033[32m'
    YELLOW  = '/033[33m'
    BLUE    = '/033[34m'
    MAGENTA = '/033[35m'
    CYAN    = '/033[36m'
    WHITE   = '/033[37m'

    @classmethod
    def c(cls, color, msg):
        return "%s%s%s" % (color, msg, cls.DEFAULT)

    def __init__(self):
        pass

    def info(self, message):
        logging.info(c(self.CYAN, "  info  ", message))

    def warn(self, message):
        logging.warn(c(self.YELLOW, "  WARNING  ", message))

    def error(self, message):
        logging.error("  ERROR  ", message)

    def critical_error(self, message):
        logging.error("  ERROR  ", message)

    def __call__(self, req, res):
        logging.info("Connection from {}".format(req.ip))
        req.log = self
