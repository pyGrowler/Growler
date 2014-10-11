#
# growler/middleware/logger
#

import growler

def middleware(cls):
  """Class decorator for classes which contain middleware functions"""
  if isinstance(cls, int):
    print ("class middleware: ", cls, cls.__name__, cls.__qualname__)
  else:
    print ("      middleware: ", cls, cls.__name__, cls.__qualname__)
  return cls

from .logger import Logger
from .cookieparser import CookieParser
from .responsetime import ResponseTime

__all__ = ['Logger']
