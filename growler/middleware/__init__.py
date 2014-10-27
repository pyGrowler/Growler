#
# growler/middleware/__init__.py
#

import growler

def middleware(cls):
  """Class decorator for classes which contain middleware functions"""
  if isinstance(cls, int):
    print ("class middleware: ", cls, cls.__name__, cls.__qualname__)
  else:
    print ("      middleware: ", cls, cls.__name__, cls.__qualname__)
  return cls

from .static import Static
from .logger import Logger
from .renderer import Renderer
from .session import (Session, SessionStorage, DefaultSessionStorage)
from .cookieparser import CookieParser
from .responsetime import ResponseTime
from .timer import Timer

__all__ = ['Logger']
