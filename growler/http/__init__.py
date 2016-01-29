#
# growler/http/__init__.py
#
# flake8: noqa
#
"""
Sub-package dealing with HTTP implementation. In this pacakge we have the
asyncio protocol, server, parser, and request and response objects.
"""

from .parser import Parser
from .request import HTTPRequest
from .response import HTTPResponse
from .protocol import GrowlerHTTPProtocol
from .errors import __all__ as http_errors
from .status import Status
from .methods import HTTPMethod

from http.server import BaseHTTPRequestHandler

import mimetypes


mimetypes.init()

__all__ = [
    'HTTPRequest',
    'HTTPResponse',
    'HTTPParser',
    'HttpStatusPhrase',
    'GrowlerHTTPProtocol',
]

__all__.extend(http_errors)

MAX_REQUEST_LENGTH = 4 * (2 ** 10)  # 4KB
MAX_POST_LENGTH = 2 * (2 ** 20)     # 2MB

RESPONSES = BaseHTTPRequestHandler.responses

HttpStatusPhrase = Status.Phrase
