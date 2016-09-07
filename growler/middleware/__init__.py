#
# growler/middleware/__init__.py
#
# flake8: noqa
#
"""
Implementation of default middleware along with the virtual package for
others to extend growler middleware with their own packages.
"""

import growler

from .auth import Auth
from .static import Static
from .logger import Logger
from .renderer import (
    Renderer,
    StringRenderer,
)
from .session import (
    Session,
    SessionStorage,
    DefaultSessionStorage,
)
from .cookieparser import CookieParser
from .responsetime import ResponseTime


__all__ = ['Logger']
