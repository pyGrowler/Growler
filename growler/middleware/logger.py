#
# growler/middleware/logger.py
#
# flake8: noqa
#

from termcolor import colored

import asyncio


class Logger():

    # Not pep8 but much better!
    DEFAULT = '/033[30m'
    RED     = '/033[31m'
    GREEN   = '/033[32m'
    YELLOW  = '/033[33m'
    BLUE    = '/033[34m'
    MAGENTA = '/033[35m'
    CYAN    = '/033[36m'
    WHITE   = '/033[37m'

    def __init__(self):
        pass

    def info(self, message):
        return colored("  info  ", 'cyan') + message

    def warn(self, message):
        return colored("  warning  ", 'yellow') + message

    def error(self, message):
        return colored("  error  ", 'red') + message

    def critical_error(self, message):
        return colored("  ERROR  ", 'red') + message

    @asyncio.coroutine
    def __call__(self, req, res):
        print(self.info("Connection from {}".format(req.ip)))

    def mw(self, req, res):
        print("[Logger] % %" % (req, res))
